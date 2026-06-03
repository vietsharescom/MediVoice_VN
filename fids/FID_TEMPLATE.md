# FID-VN-NNN — [Tên Feature]
# Feature Intent Document | ISO_VN v1.0
# Status: DRAFT → APPROVED → DONE

| Field | Value |
|---|---|
| FID ID | FID-VN-NNN |
| Layer | L{N} |
| LOC estimate | ~{N} LOC |
| Risk level | LOW / MEDIUM / HIGH |
| Created | YYYY-MM-DD |
| Approved by | Andy Phan |
| Approved date | YYYY-MM-DD |

---

## WHY (Tại sao cần feature này?)

...

## WHAT (Feature làm gì? Input/Output?)

Input: ...
Output: ...
Side effects: ...

## ACCEPTANCE CRITERIA (Khi nào gọi là DONE?)

- [ ] Tests 100% PASS
- [ ] CEER không tăng sau khi thêm feature
- [ ] CHANGELOG entry
- [ ] Không vi phạm frozen layers

## RISKS

| Risk ID | Mô tả | Kiểm soát |
|---|---|---|
| R-... | ... | ... |

## TESTS REQUIRED

- [ ] Unit test: test_{layer}_{feature}.py
- [ ] Integration test nếu cần
- [ ] Pipeline integrity test vẫn PASS

## COMMIT FORMAT

```
feat(L{N}): {mô tả} [FID-VN-NNN]
```

---

*FID Template | ISO_VN v1.0 | MediVoice VN*
