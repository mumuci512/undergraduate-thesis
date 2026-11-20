$ErrorActionPreference = 'Stop'
$auditDir = 'C:\undergraduate_thesis\05_writing\Templates\format_audit_20261117'
$source = (Get-ChildItem -LiteralPath 'C:\undergraduate_thesis\05_writing\Templates' -Filter '2*.doc' | Select-Object -First 1).FullName
$word = $null
$doc = $null
try {
  $word = New-Object -ComObject Word.Application
  $word.Visible = $false
  $word.DisplayAlerts = 0
  $word.AutomationSecurity = 3
  $doc = $word.Documents.Open($source, $false, $true, $false)
  try { $word.ActiveWindow.View.ShadeEditableRanges = $false } catch {}
  try { $word.ActiveWindow.View.ShowBookmarks = $false } catch {}
  try { $doc.ShowRevisions = $false } catch {}
  $doc.Repaginate()
  $result = [ordered]@{ WordVersion=$word.Version; Pages=$doc.ComputeStatistics(2); Sections=@(); Paragraphs=@(); Tables=@(); Shapes=@(); InlineShapes=@() }
  foreach ($section in $doc.Sections) {
    $setup = $section.PageSetup
    $props = [ordered]@{}
    foreach ($name in @('PageWidth','PageHeight','TopMargin','BottomMargin','LeftMargin','RightMargin','Gutter','HeaderDistance','FooterDistance','DifferentFirstPageHeaderFooter','OddAndEvenPagesHeaderFooter','VerticalAlignment','SectionStart','LayoutMode','LinesPage','CharsLine','MirrorMargins')) { try { $props[$name]=$setup.$name } catch {} }
    $props['Headers'] = @()
    $props['Footers'] = @()
    foreach ($kind in @('Headers','Footers')) {
      foreach ($item in $section.$kind) {
        $entry = [ordered]@{ Index=$item.Index; Exists=$item.Exists; Text=$item.Range.Text; Shapes=$item.Shapes.Count; InlineShapes=$item.Range.InlineShapes.Count; Fields=@() }
        foreach ($field in $item.Range.Fields) { $entry.Fields += @{Code=$field.Code.Text;Result=$field.Result.Text} }
        $props[$kind] += $entry
      }
    }
    $result.Sections += $props
  }
  $i = 0
  foreach ($p in $doc.Paragraphs) {
    $i++
    $r = $p.Range
    $f = $r.Font
    $pf = $p.Format
    $result.Paragraphs += [ordered]@{ Index=$i; Start=$r.Start; End=$r.End; Text=$r.Text; Page=$r.Information(3); X=$r.Information(5); Y=$r.Information(6); Style=$r.Style.NameLocal; Font=$f.Name; FontFarEast=$f.NameFarEast; FontAscii=$f.NameAscii; Size=$f.Size; Bold=$f.Bold; Color=$f.Color; Underline=$f.Underline; Spacing=$f.Spacing; Scaling=$f.Scaling; Alignment=$pf.Alignment; LeftIndent=$pf.LeftIndent; RightIndent=$pf.RightIndent; FirstLineIndent=$pf.FirstLineIndent; SpaceBefore=$pf.SpaceBefore; SpaceAfter=$pf.SpaceAfter; LineSpacingRule=$pf.LineSpacingRule; LineSpacing=$pf.LineSpacing; KeepTogether=$pf.KeepTogether; KeepWithNext=$pf.KeepWithNext; PageBreakBefore=$pf.PageBreakBefore; WidowControl=$pf.WidowControl; DisableLineHeightGrid=$pf.DisableLineHeightGrid; BottomBorderStyle=$pf.Borders.Item(-3).LineStyle; BottomBorderWidth=$pf.Borders.Item(-3).LineWidth }
  }
  foreach ($table in $doc.Tables) {
    $t=[ordered]@{Rows=$table.Rows.Count; Columns=$table.Columns.Count; Width=$table.PreferredWidth; WidthType=$table.PreferredWidthType; TopPadding=$table.TopPadding; BottomPadding=$table.BottomPadding; LeftPadding=$table.LeftPadding; RightPadding=$table.RightPadding; Alignment=$table.Rows.Alignment; LeftIndent=$table.Rows.LeftIndent; Borders=@(); RowDetails=@()}
    foreach ($border in $table.Borders) { $t.Borders += @{Type=$border.Type; Style=$border.LineStyle; Width=$border.LineWidth; Color=$border.Color} }
    foreach ($row in $table.Rows) { $t.RowDetails += @{Height=$row.Height; HeightRule=$row.HeightRule; AllowBreakAcrossPages=$row.AllowBreakAcrossPages; Cells=@($row.Cells | ForEach-Object { @{Text=$_.Range.Text; Width=$_.Width; VerticalAlignment=$_.VerticalAlignment; TopPadding=$_.TopPadding; BottomPadding=$_.BottomPadding; LeftPadding=$_.LeftPadding; RightPadding=$_.RightPadding} })} }
    $result.Tables += $t
  }
  foreach ($shape in $doc.Shapes) { $result.Shapes += @{Name=$shape.Name;Type=$shape.Type;Width=$shape.Width;Height=$shape.Height;Left=$shape.Left;Top=$shape.Top;RelativeHorizontalPosition=$shape.RelativeHorizontalPosition;RelativeVerticalPosition=$shape.RelativeVerticalPosition;Page=$shape.Anchor.Information(3);Anchor=$shape.Anchor.Start} }
  foreach ($shape in $doc.InlineShapes) { $result.InlineShapes += @{Type=$shape.Type;Width=$shape.Width;Height=$shape.Height;Page=$shape.Range.Information(3);Start=$shape.Range.Start} }
  $result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath "$auditDir\word_native.json" -Encoding UTF8
  $doc.ExportAsFixedFormat("$auditDir\word_original.pdf", 17)
  $doc.SaveAs2("$auditDir\word_converted.docx", 16)
  Write-Output ('Exported Word template: ' + $result.Pages + ' pages; ' + $result.Paragraphs.Count + ' paragraphs; ' + $result.Tables.Count + ' tables.')
} finally {
  if ($null -ne $doc) { $doc.Close(0); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($doc) }
  if ($null -ne $word) { $word.Quit(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) }
}
