module.exports = {
  plugins: [require.resolve("@trivago/prettier-plugin-sort-imports")],
  importOrder: ["^[@a-z]", "^[./]"],
  importOrderSeparation: true,
  importOrderSortSpecifiers: true,
};
