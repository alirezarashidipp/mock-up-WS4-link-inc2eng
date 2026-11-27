// Offline counterpart to app/finding/clean_names.py and match_rows.py for one field.
(() => {
  'use strict';

  const removedWords = new Set([
    'a', 'an', 'and', 'of', 'on', 'the', 'holding', 'holdings', 'llm', 'partners', 'solution', 'solutions',
    'vendor', 'global', 'bureau',
    'company', 'corp', 'corporation', 'inc', 'incorporated', 'limited', 'llc', 'llp', 'ltd', 'plc',
  ]);
  // Cleaned whole-name replacements from config/supplier_aliases.yml, applied once to incidents.
  const aliases = Object.freeze({
    gcp: 'google',
    azure: 'microsoft',
    bt: 'british telecom',
    successfactors: 'sap',
    'amazon web services': 'aws',
  });
  const separators = /[;,:؛،()[\]{}\-–—_/\\|"“”]/gu;
  const whitespace = /[\p{White_Space}\u001c-\u001f]+/u;
  const fuzzyThreshold = 0.50;

  function cleanName(value) {
    const words = String(value ?? '').toLowerCase().replaceAll('.', '')
      .replaceAll('&', ' and ').replace(separators, ' ').split(whitespace);
    return words.filter(word => word && !removedWords.has(word)).join(' ');
  }

  function replaceAlias(cleanedName) {
    return Object.hasOwn(aliases, cleanedName) ? aliases[cleanedName] : cleanedName;
  }

  function similarity(queryCharacters, candidateCharacters) {
    // Keep two rows of the Levenshtein distance matrix. Arrays hold Unicode code points.
    let previous = Array.from({ length: candidateCharacters.length + 1 }, (_, index) => index);
    let current = new Array(previous.length);
    for (let i = 1; i <= queryCharacters.length; i++) {
      current[0] = i;
      for (let j = 1; j <= candidateCharacters.length; j++) {
        const substitution = queryCharacters[i - 1] === candidateCharacters[j - 1] ? 0 : 1;
        current[j] = Math.min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + substitution);
      }
      [previous, current] = [current, previous];
    }
    const length = Math.max(queryCharacters.length, candidateCharacters.length);
    return (length - previous[candidateCharacters.length]) / length;
  }

  function substringExcerpt(reference, offset, length) {
    // Convert offsets in the compact name back to the cleaned field, retaining internal spaces.
    const positions = [];
    for (let index = 0; index < reference.length; index++) {
      if (reference[index] !== ' ') positions.push(index);
    }
    return reference.slice(positions[offset], positions[offset + length - 1] + 1);
  }

  function compare(rawIncidentName, rawEngagementField) {
    const inputWords = String(rawIncidentName ?? '').split(whitespace).filter(Boolean);
    const cleanIncident = cleanName(rawIncidentName);
    const cleanReference = cleanName(rawEngagementField);
    const compactReference = cleanReference.replaceAll(' ', '');
    const result = {
      cleanIncident, queryName: '', query: '', cleanReference, compactReference,
      method: 'NO_MATCH', reason: '', matchedText: '', score: null,
    };
    if (!inputWords.length) return { ...result, method: 'SKIPPED', reason: 'skipped_blank' };
    if (inputWords.length === 1 && inputWords[0].toLowerCase() === 'unknown') {
      return { ...result, method: 'SKIPPED', reason: 'skipped_unknown' };
    }

    result.queryName = replaceAlias(cleanIncident);
    result.query = result.queryName.replaceAll(' ', '');
    const query = result.query;
    if (!query) return { ...result, method: 'INVALID_NAME', reason: 'empty_query' };
    if (!compactReference) return { ...result, reason: 'empty_reference' };
    if (query === compactReference) {
      return { ...result, method: 'EXACT', reason: 'equal', matchedText: cleanReference };
    }

    const queryCharacters = Array.from(query);
    const words = cleanReference.split(' ');
    const offset = compactReference.indexOf(query);
    if (offset !== -1) {
      if (queryCharacters.length > 4) {
        return { ...result, method: 'SUBSTRING', reason: 'embedded',
          matchedText: substringExcerpt(cleanReference, offset, query.length) };
      }
      if (words.includes(query)) {
        return { ...result, method: 'SUBSTRING', reason: 'whole_word', matchedText: query };
      }
      return { ...result, reason: 'short_inside_word' };
    }
    if (queryCharacters.length < 5) return { ...result, reason: 'short_no_match' };

    let bestScore = null;
    for (let start = 0; start < words.length; start++) {
      const candidateCharacters = [];
      for (let end = start; end < words.length; end++) {
        for (const character of words[end]) candidateCharacters.push(character);
        if (candidateCharacters.length * fuzzyThreshold > queryCharacters.length) break;
        if (queryCharacters.length * fuzzyThreshold > candidateCharacters.length) continue;
        const score = similarity(queryCharacters, candidateCharacters);
        if (score >= fuzzyThreshold) {
          return { ...result, method: 'FUZZY', reason: 'fuzzy_pass',
            matchedText: words.slice(start, end + 1).join(' '), score };
        }
        bestScore = bestScore === null ? score : Math.max(bestScore, score);
      }
    }
    return { ...result, reason: bestScore === null ? 'fuzzy_length' : 'fuzzy_below', score: bestScore };
  }

  window.FindingLab = Object.freeze({ compare, cleanName, replaceAlias, aliases, fuzzyThreshold });
})();
