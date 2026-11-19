# Stage-one matching scenarios

Each row is an independent example. **Name** means `THIRD_PARTY_NAME`; **Normalized name** means `THIRD_PARTY_NORMALIZED_NAME`. Excel copies the winning raw reference into `found_name_in_source`.

| Scenario | Input raw | Input normalized | Reference raw | Reference normalized | Excel result |
|---|---|---|---|---|---|
| 1. Case and spacing | PINGidentity | pingidentity | Ping Identity | pingidentity | `EXACT` on Name |
| 2. Punctuation and suffix | The North-Star (Solutions); PLC | northstar | North Star | northstar | `EXACT` on Name |
| 3. YAML alias | GCP | googlecloudplatform | Google Cloud Platform | googlecloudplatform | `EXACT` on Name |
| 4. Both fields equal the input | Acme | acme | ACME / Acme | acme / acme | `EXACT` on Name wins |
| 5. Exact match in the second field | Orion | orion | Orion UK / ORION | orionuk / orion | `EXACT` on Normalized name |
| 6. Both fields contain the input | Microsoft | microsoft | Microsoft UK Ltd / MICROSOFT EMEA | microsoftukltd / microsoftemea | `PARTIAL` on Normalized name wins |
| 7. Only Name contains the input | Apex | apex | Apex Taiwan Ltd | apextaiwanltd | `PARTIAL` on Name |
| 8. Typo | Microsfot | microsfot | Microsoft Ltd | microsoftltd | `PARTIAL` on Normalized name. Fuzzy score against `microsoft` is 0.78. |
| 9. Short name inside another word | BT | bt | DEBT | debt | `PARTIAL` on Normalized name. Possible false positive. |
| 10. Incident class is HSBC | Acme | Skipped | Acme | acme | Zero rows. Class filter excludes the incident. |
| 11. Short name with a typo | IBM | ibm | IBN | ibn | Zero rows. Fuzzy matching requires at least five characters. |
| 12. Two engagements | Acme | acme | ENG-1: Acme / ENG-2: Acme UK Limited | acme / acmeuklimited | Two rows: ENG-1 `EXACT`, ENG-2 `PARTIAL`, both on Name. |

In scenarios 4-6, the two references are listed in source-field order: Name / Normalized name.
