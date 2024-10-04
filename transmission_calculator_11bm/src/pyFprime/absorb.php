<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<html>
	<head>
		<title>Compute X-ray Absorption</title>
		<link rel="shortcut icon" href="../images/favicon.ico"> 
		<link href="../stylesheet.css" rel="stylesheet" type="text/css">
		
		<!--javascript to toggle display of hidden text--->
		<script type="text/javascript">
		function toggle_visibility(id) {
		var e = document.getElementById(id);
		if(e.style.display == 'none')
		e.style.display = 'block';
		else
		e.style.display = 'none';
		}
		</script>
        
	</head>

<body>
    
    <table width="100%" border="0" cellpadding="0" cellspacing="3">
<!-------TOP HEADER-----------------------------------------------TOP HEADER--->
        <tr> 
            <td colspan="2">
            <table width="100%"  border="0" cellspacing="0" cellpadding="0">
                <tr class="headerBkgd" valign="middle">
                    <td class="leftbanner"><a href="http://www.anl.gov/"><img src="../images/argonne_header_logo.jpg" alt="Argonne National Laboratory" width="227" height="100" border="0"></a></td>
                        <td><p>
                            <a href="http://www.aps.anl.gov" class="sectionTitle">Advanced Photon Source<br></a>
                            <img src="../images/spacer.gif" width="1" height="5" border="0" alt=""><br>
			    <a href="http://11bm.xray.aps.anl.gov" class="whiteText">Compute X-ray Absorption<br></a>
                        </p></td>
                    <td class="rightbanner"><a href="http://www.energy.gov/"><img src="../images/header_doe.gif" alt="US Dept. of Energy" border="0"></a></td>
                </tr>
            </table>
            </td>
        </tr>
<tr valign="top">
    <td>
    <table width="100%" border="0" cellpadding="5" cellspacing="0" bgcolor=#F1EEE8>
        <tr> 
            <td class="mainbody">
  
<a name="MainContent"></a>
   <blockquote><font face="arial, helvetica, sans-serif">

<?php
$mode = strip_tags($_GET['mode']);
if ($mode == "") {
#===============================================================================
# initial call, put up the web form
#===============================================================================
?>

<!-----MAIN BODY----------------------------------------------------MAIN BODY-->

<h2>Compute X-ray Absorption</h2>
   <FORM METHOD="GET" ACTION="<?php echo $_SERVER['PHP_SELF']; ?>">
   <INPUT TYPE="hidden" NAME="mode" value="calc">

<B>Select X-ray Wavelength or Energy:</B>
   <!-----toggled "details" text ---->
   <a onclick="toggle_visibility('verbose_spectrum');" style="color:blue; font-size:smaller" > (click for details)</span></a>
   <br>
   <span id="verbose_spectrum" style="display:none; color:#444444; font-size:small; font-style:normal">
	Select Wavelength or Energy from the pull-down menu
	<br>Enter valid X-ray wavelength (or energy) in the range 0.05 - 3.0 &Aring; (248 - 4.13keV)
	<br>Valid range is reduced for high Z elements (Z > 78), see 'more information' in About section below for details
	<br></span>
   <!------->
   <!---?? Add flag to URL to define spectrumtype selection ??---->
   <SELECT NAME="spectrumtype">
   <OPTION VALUE="Wavelength" SELECTED> Wavelength (&Aring;)
   <OPTION VALUE="Energy"> Energy (keV)
   </SELECT>
   <!------->
   <?php
   if (!isset($_GET['spectrum'])) {
	$_GET['spectrum']="0.41";
   }
   ?>
   <input name="spectrum" size=20 value="<?php print $_GET['spectrum']?>">
   <!------->
   <!-----<input name="spectrum" size=20 value="0.41">-->
<BR>
<BR>

<B>Chemical Formula:</B>
   <!-----toggled "details" text ---->
   <a onclick="toggle_visibility('verbose_formula');" style="color:blue; font-size:smaller" > (click for details)</span></a>
   <br>
   <span id="verbose_formula" style="display:none; color:#444444; font-size:small; font-style:normal">
	Accepts all elemental symbols in the range H (Z=1) to Cf (Z=98)
	<br>Note: absorption for H and He is assumed zero and not included in calculation
	<br>Fractional formula unit occupancies are rounded to the nearest hundredth (0.01)
	<br>Entered formula (assuming unit cell Z = 1) is used to estimate sample density if "packed faction" is selected below
	<br></span>
   <!------->
   <div style="font-size:small;"><i>enter using element chemical symbol and formula unit occupancy, e.g. YBa2Cu3O6.5 (proper capitalization is required)</i></div>
   <input name="formula" size=50 value="">
<BR>
<BR>

<B>Sample Radius:</B>
   <!-----toggled "details" text ---->
   <a onclick="toggle_visibility('verbose_radius');" style="color:blue; font-size:smaller" > (click for details)</span></a>
   <br>
   <span id="verbose_radius" style="display:none; color:#444444; font-size:small; font-style:normal">
	Enter radius (in millimeters) of capillary used for transmission geometry (Debye-Scherrer) powder X-ray diffraction measurement
	
	<br></span>
   <!------->
   <?php
   if (!isset($_GET['radius'])) {
	$_GET['radius']="0.40";
   }
   ?>
   <input name="radius" size=5 value="<?php print $_GET['radius']?>"><span style="font-size:small;"><i>  capillary radius in mm</i></span>
   <!------->
   <!--<input name="radius" size=5 value="0.40"><span style="font-size:small;"><i>  capillary radius in mm</i></span>-->
<BR>
<BR>
 
<B>Sample Density or Packing Fraction</B>
   <!-----toggled "details" text ---->
   <a onclick="toggle_visibility('verbose_packing');" style="color:blue; font-size:smaller" > (click for details)</span></a>
   <br>
   <span id="verbose_packing" style="display:none; color:#444444; font-size:small; font-style:normal">
	Select 'Sample Density' or 'Packing Fraction' from the pull-down menu
	<br>'Sample Density' is more accurate, however 'Packing Fraction' provides a good estimate if real packed sample density is not known.
	<br>'Sample Density' refers to the actual measured density (in g/cc) of a capillary sample loaded with powder
	<br>'Packing Fraction' refers to the estimated packing fraction of sample powder in the capillary (often ~ 0.6)
	<br>When 'Packing Fraction' is selected, the sample density is estimated assuming 10 cubic &Aring; per atom in the entered chemical formula
	<br>The accuracy of this estimate is typically good to &plusmn; &asymp; 25% of experimental density 
	<br></span>
   <!------->
   <!---?? Add flag to URL to define densitytype selection ??---->
<div style="font-size:small;"><i>enter measured sample density or estimated packing fraction (often ~0.6)</i></div>
   <SELECT NAME="densitytype">
   <OPTION VALUE="RHO"> Sample Density (g/cc)
   <OPTION SELECTED> Packed Fraction (0.0 - 1.0)
   </SELECT>
   <!------->
   <?php
   if (!isset($_GET['density'])) {
	$_GET['density']="0.5";
   }
   ?>
   <input name="density" size=10 value="<?php print $_GET['density']?>">
   <!------->
   <!--<input name="density" size=10 value="0.5">-->
<BR>
<BR>
 
<INPUT TYPE="submit" VALUE="Compute" NAME="submit">
<INPUT TYPE="reset" VALUE="Clear Form">
</form>

<HR>

<span style="font-size:small;"><b>About:</B> This routine estimates capillary sample absorption for transmission geometry (Debye-Scherrer) powder X-ray diffraction measurements.

<!-----toggled "details" text ---->
<a onclick="toggle_visibility('verbose_details');" style="color:blue; font-size:inherit" >
<br>(click here for more information)</a>
<span id="verbose_details" style="display:none; color:#444444; font-size:small; font-style:normal">
Capillary sample absorption is estimated (based on user supplied data and calculated f' & f" values) for elements between Li - Cf and in the X-ray wavelength range 0.05 - 3.0&Aring; (248-4.13keV) using the Cromer & Liberman algorithm <a href="http://dx.doi.org/10.1107/S0567739481000600" target="blank">(reference: Acta Cryst. 1981 v.A37, p.267)</a> and orbital cross-section tables. Note that the Cromer - Liberman algorithm fails in computing f' for wavelengths < 0.16 &Aring; (> 77.48 keV) for the heaviest elements (Au-Cf) and fails to correctly compute f', f" and mu for wavelengths > 2.67 &Aring; (< 4.64 keV) for very heavy elements (Am-Cf).</span>
   <!------->
   <p>
<span style="font-size:inherit;">Web utility created by Robert B. Von Dreele, Matthew R. Suchomel and Brian H. Toby, based on the python software package <i>Absorb</i> <a href="https://subversion.xray.aps.anl.gov/trac/pyFprime/browser/trunk/" target="blank">(download here)</a>.</span>

<p>
<a href="http://11bm.xray.aps.anl.gov/absorption.html">&raquo; Return to 11-BM X-ray absorption webpage</a>

<!-----tLast Modified ---->

<p>
<div style="font-size:small; color:#444444;"> <B>New feature</B>: define your own custom absorb.php bookmark with default wavelength settings (or sample radius etc)</div>
<div> Example: try the URL <a href="http://11bm.xray.aps.anl.gov/absorb/absorb.php?spectrum=1.54&radius=0.5&density=1.0"> http://11bm.xray.aps.anl.gov/absorb/absorb.php?<b>spectrum=1.54&radius=0.5&density=1.0</b></a></div>
<p>
<div style="font-size:small; color:#444444;"> Last Modified: Feb 2013 </div>
<br>

<?php
 } else {
#===============================================================================
# 2nd call perform the computation
#===============================================================================
  print "<h2>X-ray Absorption Computation</h2>";
  $now = date("ymdhis", time());
  $imageroot = "Abs" . $now . getmypid() . ".png";
  $imageloc="/tmp/absorbplots/";
  $imagefile=$imageloc . $imageroot;
  if (file_exists($imagefile)) {
    unlink($imagefile);
  } else {
    if (! file_exists($imageloc)) {
      mkdir($imageloc);
    }
  }
  $type = strip_tags($_GET['spectrumtype']);
  $value = strip_tags($_GET['spectrum']);
  $formula = strip_tags($_GET['formula']);
  $radius = strip_tags($_GET['radius']);
  
  if (strstr($type, "Wavelength")) {
    $iwave = 1;
  } else {
    $iwave = 0;
  }
  $densitytype = strip_tags($_GET['densitytype']);
  $density = strip_tags($_GET['density']);
  if (strstr($densitytype, "RHO")) {
    $irho = 0;
  } else {
    $irho = 1;
  }
  
  $descriptorspec = array(
   0 => array("pipe", "r"),  // stdin is a pipe that the child will read from
   1 => array("pipe", "w"),  // stdout is a pipe that the child will write to
   2 => array("file", "/tmp/absorbplots/error-output.txt", "w") // stderr is a file to write
			  );
  #$process = proc_open('/usr/local/bin/python /home/joule/WEB11BM/www/absorb/runweb.py', $descriptorspec, $pipes);
  #$process = proc_open('/usr/bin/python /home/joule/WEB11BM/www/absorb/runweb.py', $descriptorspec, $pipes);
  $process = proc_open('/APSshare/epd/rh6-x86/bin/python /home/joule/WEB11BM/www/absorb/runweb.py', $descriptorspec, $pipes);

  if (is_resource($process)) {
    $fp = $pipes[0];
    fwrite($fp, $formula . "\n");
    fwrite($fp, $radius . "\n");
    fwrite($fp, $imagefile . "\n");
    fwrite($fp, $iwave . "\n");
    fwrite($fp, $value . "\n");
    fwrite($fp, $irho . "\n");
    fwrite($fp, $density . "\n");
    fclose($pipes[0]);
    while(!feof($pipes[1])) { 
      print fgets($pipes[1]);
    }
    if (file_exists($imagefile)) {
      print '<P><img src="plotimg/' . $imageroot . '">';
      print "<BR><I>".
	"The plot above shows the absorption for each input element and for " . 
	"the specified composition as a function of X-ray wavelength/energy." .
	" The blue dotted line indicates a muR value of 1. In a capillary " . 
	"(Debye-Scherrer) geometry, it is ideal when muR is 1 or below, as ".
	"sample absorption is minimal and no correction is usually needed. " .
	"The red dotted line indicates a muR value of 5. For muR >= 5, ".
	" measurements are generally not possible in a capillary ".
	"geometry, as there will be very severe levels of absorption and ".
	"corrections are inaccurate.</I>";
    } else {
      print "<H4>Sorry; there is an error with your entered information or with this webpage.";
      print "<H4>Please fix your information and try again, or send details of the webpage error to 11-BM@aps.anl.gov.";
      // debug code
      $contents = file("/tmp/absorbplots/error-output.txt");
      $string = implode($contents);
      print "<PRE>";
      echo $string;
      print "</PRE>";
    }
  } else {
    print "no process created<BR>";
  }
 }
?>
                        </td> 
                    </tr> 
                </table>
            
                <img src="../images/spacer.gif" width="800" height="1" border="0" alt=""> 
            </td>
        </tr>
        
<!---------Footer------------------------------------------------------Footer-->  
        <tr valign="top"> 
            <td colspan="2"><table width="100%" border="0" cellspacing="0" cellpadding="0"> 
                
                <tr> 
                    <td colspan="2" align="left" style="border-top:1px solid #666;font-size:9px;color:#bbb;"> &nbsp; </td>            
                </tr>
                
                <tr>
                    <td>&nbsp;</td>
                        <td align="center" style="width:100%;">
                            <a href="http://www.sc.doe.gov/" class="footlink">U.S. Department of Energy Office of Science</a>&nbsp;<div class="foot">|</div>&nbsp;
                            <a href="http://www.sc.doe.gov/bes/" class="footlink">Office of Basic Energy Sciences</a>&nbsp;<div class="foot">|</div>&nbsp;
                            <a href="http://www.uchicagoargonnellc.org/" class="footlink">UChicago Argonne LLC</a>
                        </td>
                    <td>&nbsp;</td>
                </tr>
                
                <tr>
                    <td align="center">&nbsp;</td>
                        <td align="center" style="width:100%;">
                            <a href="http://www.anl.gov/notice.html" class="footlink">Privacy &amp; Security Notice</a>&nbsp;<div class="foot">|</div>&nbsp;
                            <a href="http://www.aps.anl.gov/Users/Contacts/" class="footlink">Contact Us</a>&nbsp;<div class="foot">|</div>&nbsp;
                            <a href="http://www.aps.anl.gov/site_map.html" class="footlink">Site Map</a>
                        </td>
                    <td >&nbsp;</td>
                </tr>
            </table></td> 
        </tr> 

    </table>

<!--needed for google analytics webpage tracking --->
<?php
include ("../googleanalyticstracking.php");
?>   

</body>
</html>