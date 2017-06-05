$python = "C:\Python27\python.exe"
$processing_script = "c:\PRIMA\scripts\vampire\prima_process.py"

#$ref_date = (Get-Date).AddDays(-48)
$ref_date = [DateTime]'2016-12-18'
#get year from last month
$YEARNOW = ($ref_date).Year
echo $YEARNOW

#get month from last month
$MONTHNOW = (($ref_date).Month).ToString("00")
echo $MONTHNOW


$start_year = "$YEARNOW-01-01"
$time_span = ($ref_date) - [DateTime]($start_year)
$16days = ($time_span.Days)/16
$remainder = ($time_span.Days)%16
if ($remainder -ne 0) {
  $16day_date = ($ref_date).AddDays(-$remainder)
} else {
  $16day_date = $ref_date
}
$YEARNOW = $16day_date.Year
$MONTHNOW = ($16day_date.Month).ToString("00")
$DAYNOW = ($16day_date.Day).ToString("00")
echo $time_span
echo "ref_date:" $ref_date
echo "remainder:" $remainder
echo "16Day Date:" $16day_date

#check if the final tif (lka_phy_MOD13Q1.$YEARNOW$MONTHNOW$DAYNOW.250m_16_days_EVI_EVI_VCI_VHI.tif) already exist
$vhi_geoserver_path = "C:\Program Files (x86)\GeoServer 2.11.0\data_dir\data\vhi\lka_phy_MOD13Q1.$YEARNOW$MONTHNOW$DAYNOW.250m_16_days_EVI_EVI_VCI_VHI.tif"
echo $vhi_geoserver_path
if (Test-Path $vhi_geoserver_path) {
  echo "File exists"
}
Else {
  echo "VHI for $YEARNOW-$MONTHNOW-$DAYNOW does not exist yet. Try processing."
  & $python $processing_script -c "Sri Lanka" -p vhi -o c:\PRIMA\configs\config_vhi_current.yml -d $YEARNOW-$MONTHNOW-$DAYNOW
}
