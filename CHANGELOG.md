# Changelog

## 1.0.0 (2020-07-02)
- Fail if no data rows are received (closes: #4)
- Catch more (connection, authentication,...) problems during loading of data and
  retry in that case (closes: #2, #4)
- Fix problem with interpreting float numbers which had both `,` and `.` in it. If your
  spreadsheet is e.g. German, you need to set the thousand separator in your column spec:
  '...f(thousands_separator=.)...' (thanks to @hz-lschick for the bugreport)
- Fix service account mara integration (#6)
- Replace data_integration with mara_pipelines 3.0.0 (#8)

## 0.1.0 (2020-03-25)

- Move to Github
