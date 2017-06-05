$python = "C:\Python27\python.exe"
$processing_script = "c:\PRIMA\scripts\vampire\prima_process.py"

#$ref_date = (Get-Date).AddDays(-10)
$ref_date = [DateTime]'2017-05-21'

#get year from last month
$YEARNOW = $ref_date.Year
echo $YEARNOW

#get month from last month
$MONTHNOW = ($ref_date.Month).ToString("00")
echo $MONTHNOW

$DAYNOW = $ref_date.Day
If($DAYNOW -le 10) {
  $dekad = 1
  $dekad_day = "01"
}
ElseIf($DAYNOW -le 20) {
  $dekad = 2
  $dekad_day = 11
}
Else {
  $dekad = 3
  $dekad_day = 21
}
$DAYNOW = $DAYNOW.ToString("00")
echo $DAYNOW
echo $dekad

#check if the final tif (idn_cli_chirps-$YEARNOW$MONTHNOW.spi.tif) already exist
$spi_geoserver_path = "C:\Program Files (x86)\GeoServer 2.11.0\data_dir\data\spi\lka_cli_chirps-v2.0.$YEARNOW$MONTHNOW$dekad_day.spi.tif"
echo $spi_geoserver_path
if (Test-Path $spi_geoserver_path) {
  echo "File exists"
}
Else {
  echo "Standardized Precipitation Index for $YEARNOW-$MONTHNOW-$dekad_day does not exist yet. Try processing."
  & $python $processing_script -c "Sri Lanka" -p spi -i dekad -o c:\PRIMA\configs\config_spi_current.yml -d $YEARNOW-$MONTHNOW-$dekad_day
}
