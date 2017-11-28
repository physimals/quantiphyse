"""
Create an MSI package using the WIX toolset

We adopt the rule of 'one file per component' as suggested although this requires thousands
of components. Generation of GUIDs is accomplished by using the Python UUID library to generate 
the ID based on a hash of the file path. This should ensure that the GUIDs are specific to the
file path (as required) and also reproducible (as required). 

The same technique is used to generate the product, upgrade GUID, using fixed notional paths
for reproducibility
"""
import os, sys
import uuid
from StringIO import StringIO

# Get absolute paths to the packaging dir and the root Quantiphyse dir
pkgdir = os.path.abspath(os.path.dirname(__file__))
qpdir = os.path.abspath(os.path.join(pkgdir, os.pardir))
sys.path.append(qpdir)
import update_version

DIST_ROOT_DIR = os.path.join(qpdir, "dist")

# Path to WIX toolset - update as required
WIXDIR = "c:\Program Files (x86)/WiX Toolset v3.11/bin/"

# Main template for our WXS file - content is added using the Python
# string formatting placeholders
WXS_TEMPLATE = """
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">

   <!-- Basic product information -->
   <Product Id="%(product_guid)s" 
            UpgradeCode="%(upgrade_guid)s" 
            Name="Quantiphyse" 
            Version="%(version_str)s" 
            Manufacturer="ibme-qubic" 
            Language="1033">
      <Package Id="*" 
               InstallerVersion="200" 
               Compressed="yes" 
               Comments="Windows Installer Package"
               Platform="x64"/>
      <Media Id="1" 
             Cabinet="product.cab" 
             EmbedCab="yes"/>
      <MajorUpgrade AllowDowngrades="no" 
                    DowngradeErrorMessage="Cannot downgrade to lower version - remove old version first"
                    AllowSameVersionUpgrades="no"/>


      <Directory Id="TARGETDIR" Name="SourceDir">

        <!-- Installation registry entries and shortcut -->
        <Component Id="RegKeys" Guid="%(regkeys_guid)s" Win64="yes">
          <RegistryKey Root='HKLM' Key='Software\[Manufacturer]\[ProductName]'>
            <RegistryValue Type='string' Name='InstallDir' Value='[INSTALLDIR1]' KeyPath='yes'/>
            <RegistryValue Type='string' Name='PluginDir' Value='[INSTALLDIR1]packages\plugins'/>
          </RegistryKey>
        </Component>

        <!-- Programs menu registry entry and shortcut -->
        <Directory Id="ProgramMenuFolder" Name="Programs">
          <Directory Id="ProgramMenuDir" Name="Quantiphyse">
            <Component Id="ProgramMenuDir" Guid="%(menu_guid)s" Win64="yes">
                <RemoveFolder Id='ProgramMenuDir' On='uninstall' />
                <RegistryValue Root='HKCU' Key='Software\[Manufacturer]\[ProductName]' 
                               Type='string' Value='' KeyPath='yes'/>
            </Component>
          </Directory>
        </Directory>

        <!-- Program files -->
        <Directory Id="ProgramFiles64Folder">
%(dist_files)s 
        </Directory>
      </Directory>

      <!-- No custom features - all or nothing -->
      <Feature Id="Complete" Level="1">
%(features)s
        <ComponentRef Id="ProgramMenuDir"/>
        <ComponentRef Id="RegKeys"/>
      </Feature>

      <!-- User interface configuration -->
      <Property Id="WIXUI_INSTALLDIR" Value="INSTALLDIR" />
      <UIRef Id="WixUI_Minimal" />
      <UIRef Id="WixUI_ErrorProgressText" />
      <WixVariable Id="WixUIBannerBmp" Value="packaging/images/banner.bmp" />
      <WixVariable Id="WixUIDialogBmp" Value="packaging/images/dialog.bmp" />
      <WixVariable Id="WixUILicenseRtf" Value="packaging/LICENSE.rtf"/>
   </Product>
</Wix>"""

def get_guid(path):
    """
    Return a GUID which is reproducibly tied to a file path
    """
    return uuid.uuid5(uuid.NAMESPACE_DNS, 'quantiphyse.org/' + path)

def addSubdir(pdir, subdir, files, nfile, ndir, output, indent):
    """
    Add file componenents from a directory, recursively adding from subdirs
    """
    output.write('%s<Directory Id="INSTALLDIR%i" Name="%s">\n' % (indent, ndir, subdir))
    ndir += 1
    for dirName, subdirList, fileList in os.walk(os.path.join(pdir, subdir)):
        for fname in fileList:
            fpath = os.path.join(dirName, fname)
            guid = get_guid(fpath)
            files[fpath] = str(guid)
            output.write('%s  <Component Id="Component%i" Guid="%s" Win64="yes">\n' % (indent, nfile, str(guid)))
            if fname == "quantiphyse.exe":
                output.write('%s    <File Id="File%i" Source="%s" KeyPath="yes">\n' % (indent, nfile, fpath))
                output.write('%s      <Shortcut Id="startmenu_qp" Directory="ProgramMenuDir" Name="Quantiphyse"\n' % indent)
                output.write('%s                WorkingDirectory="INSTALLDIR" Advertise="yes"/>\n' % indent)
                output.write('%s    </File>\n' % indent)
            else:
                output.write('%s    <File Id="File%i" Source="%s" KeyPath="yes"/>\n' % (indent, nfile, fpath))
            output.write('%s  </Component>\n' % indent)
            nfile += 1
        for subdir in subdirList:
            files[subdir] = {}
            nfile, ndir = addSubdir(dirName, subdir, files[subdir], nfile, ndir, output, indent + "  ")
        break
    output.write('%s</Directory>\n' % indent)
    return nfile, ndir

def create_wxs(fname):
    """
    Create the WXS file for WIX toolset to create the MSI
    """
    formatting_values = {
        "version_str" : update_version.get_std_version().replace("-", "."),
        "product_guid" : get_guid('quantiphyse/product'),
        "upgrade_guid" : get_guid('quantiphyse/upgrade'),
        "menu_guid" : get_guid('quantiphyse/menu'),
        "regkeys_guid" : get_guid('quantiphyse/regkeys'),
    }
    
    all_files = {}
    output = StringIO()
    nfile, ndir = addSubdir(DIST_ROOT_DIR, "quantiphyse", all_files, 1, 1, output, "  " * 5)
    formatting_values["dist_files"] = output.getvalue()

    output = StringIO()
    for n in range(nfile-1):
        output.write('         <ComponentRef Id="Component%i"/>\n' % (n+1))
    formatting_values["features"] = output.getvalue()

    output = open(fname, 'w')
    output.write(WXS_TEMPLATE % formatting_values)
    output.close()

def create_msi(fname):
    """
    Create the MSI itself using WIX toolset
    """
    obj_fname = fname.replace(".wxs", ".wixobj")
    os.system('"%s/candle.exe" %s -out %s' % (WIXDIR, fname, obj_fname))
    os.system('"%s/light.exe" %s -ext WixUIExtension' % (WIXDIR, obj_fname))

wxs_fname = os.path.join(pkgdir, "quantiphyse.wxs")
create_wxs(wxs_fname)
create_msi(wxs_fname)
