// v2 - the "replacement" build, with eight planted regressions against v1 (DB-01 to DB-03, DB-06 to DB-10).
// DB-03 uses the 10% tax rate that the requirements page shows STRUCK OUT - the obsolete rule.
// DB-06 implements the STRUCK promo rule ("Up to two discount codes may be combined").
window.GENE2_DEMO = {
  variant: "v2", taxRate: 0.10, priceSortAsText: true, badgeNeverDecrements: true, validatePostcode: false,
  stackDiscounts: true, caseSensitiveSearch: true, pagerRepeatsLast: true, regionalSurchargeMissing: true,
  allowOutOfStockAdd: true,
};
