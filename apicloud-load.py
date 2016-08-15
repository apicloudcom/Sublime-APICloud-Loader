#-*-coding:utf-8-*- 
import sublime,sublime_plugin
import os,platform,re,logging,subprocess,json,sys,traceback,shutil
import sys

curDir = os.path.dirname(os.path.realpath(__file__))

settings = {}
settings = sublime.load_settings("Preferences.sublime-settings")
print(settings.get("envlang"))


html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="maximum-scale=1.0,minimum-scale=1.0,user-scalable=0,width=device-width,initial-scale=1.0"/>
    <title>title</title>
    <link rel="stylesheet" type="text/css" href="api.css"/>
    <style>
        body{
            
        }
    </style>
</head>
<body>
    
</body>
<script type="text/javascript" src="api.js"></script>
<script type="text/javascript">
    apiready = function(){
        
    };
</script>
</html>'''
class InsertApicloudHtmlCommand(sublime_plugin.TextCommand):
    def run(self, edit, user_input=None):
        self.edit = edit
        v = self.view
        v.insert(edit, 0, html)
        v.end_edit(edit)

class ApicloudNewHtmlCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        v = self.window.new_file()
        v.run_command('insert_apicloud_html')

        if len(dirs) == 1:
            v.settings().set('default_dir', dirs[0])

    def is_visible(self, dirs):
        return len(dirs) == 1 and not (settings.get("envlang") == "en" or settings.get("envlang") == "fr")

class EnApicloudNewHtmlCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        v = self.window.new_file()
        v.run_command('insert_apicloud_html')

        if len(dirs) == 1:
            v.settings().set('default_dir', dirs[0])

    def is_visible(self, dirs):
        return len(dirs) == 1 and settings.get("envlang") == "en"

class FrApicloudNewHtmlCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        v = self.window.new_file()
        v.run_command('insert_apicloud_html')

        if len(dirs) == 1:
            v.settings().set('default_dir', dirs[0])

    def is_visible(self, dirs):
        return len(dirs) == 1 and settings.get("envlang") == "fr"


############################################global function############################
def isWidgetPath(path):
    isFound = False
    appFileList=os.listdir(path)
    if 'config.xml' in appFileList and 'index.html' in appFileList:
        with open(os.path.join(path,"config.xml"),encoding='utf-8') as f:
            fileContent=f.read()
            r=re.compile(r"widget.*id.*=.*(A[0-9]{13})\"")
            searchResList=r.findall(fileContent)
            if len(searchResList)>0:
                isFound = True
    return isFound

def getWidgetPath(path):
    rootDir = os.path.abspath(path).split(os.path.sep)[0]+os.path.sep
    dirList = []
    for x in range(0,10):
        path = os.path.dirname(path)
        dirList.append(path)
        if path == rootDir:
            break

    syncPath=''
    for path in dirList:
        if isWidgetPath(path):
            syncPath = path
            break
    return syncPath

def runShellCommand(cmd,cmdLogType):
        import platform
        rtnCode=0
        stdout=''
        stderr=''

        if 'darwin' in platform.system().lower():
            p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
            stdoutbyte,stderrbyte=p.communicate()
            stdout=str(stdoutbyte)
            stderr=str(stderrbyte)
            rtnCode=p.returncode
        
        elif 'linux' in platform.system().lower():
            p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
            stdoutbyte,stderrbyte=p.communicate()
        #    stdout=str(stdoutbyte)
        #    stderr=str(stderrbyte)
            rtnCode=p.returncode    

        elif 'windows' in platform.system().lower():
            if 'logFile'==cmdLogType:
                p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
                stdoutbyte,stderrbyte=p.communicate()
                stdout=str(stdoutbyte)
                stderr=str(stderrbyte)
                rtnCode=p.returncode
            else:    
                p=subprocess.Popen(cmd,shell=False)
                p.wait()
                rtnCode=p.returncode
        else:
            print(sys._getframe().f_back.f_code.co_name +' - runShellCommand: the platform is not support - CMD='+cmd)
        return (rtnCode,stdout,stderr)  

############################################end global function############################

class ApicloudLoaderAndroidKeyCommand(sublime_plugin.TextCommand):
    """docstring for ApicloudLoaderAndroidKeyCommand"""

    def run(self, edit):
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(message)s',
            datefmt='%Y %m %d  %H:%M:%S',
            filename=os.path.join(curDir,'apicloud.log'),
            filemode='a')
        if settings.get("envlang") == "en":
            sublime.status_message(u'Starting device synchronization')
        elif settings.get("envlang") == "fr":
            sublime.status_message(u'Lancement de la synchronisation avec le terminal')
        else:
            sublime.status_message(u'开始真机同步')

        logging.debug('*'*30+'begin android key sync'+'*'*30)

        file_name=self.view.file_name()
        syncPath=getWidgetPath(file_name)
        if len(syncPath) > 0:
            logging.debug('key sync dir is '+syncPath)
            try:
                BeforeSystemRequests()
                loader = ApicloudLoaderAndroidCommand('')
                loader.load(syncPath)
            except:
                logging.debug('run: exception happened as below')
                errMsg=traceback.format_exc()
                logging.debug(errMsg)
                # print(errMsg)
                if settings.get("envlang") == "en":
                    sublime.error_message(u'Synchronization Failed')
                elif settings.get("envlang") == "fr":
                    sublime.error_message(u'Echec de la synchronisation')
                else:
                    sublime.error_message(u'真机同步出现异常')
                
            sublime.status_message(u'真机同步完成')
            logging.debug('*'*30+'android sync complete'+'*'*30)
        else:
            sublime.error_message(u'请确保当前文件所在目录正确')
        return

class ApicloudLoaderAndroidCommand(sublime_plugin.WindowCommand):
    """docstring for ApicloudLoaderAndroidCommand"""
    __adbExe='' 
    __curDir=''
    __pkgName='com.apicloud.apploader'
    __loaderName='apicloud-loader'
    __pendingVersion=''
    __cmdLogType='' #logFile
    __ignore=[".svn",".git"]
    def __init__(self,arg):
        self.__curDir=curDir
    
    def is_visible(self, dirs): 
        return len(dirs) > 0 and not (settings.get("envlang") == "en" or settings.get("envlang") == "fr")

    def is_enabled(self, dirs):
        if 0==len(dirs):
            return False
        appFileList=os.listdir(dirs[0])
        if 'config.xml' in appFileList:
            return True
        return False

    def run(self, dirs):
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(message)s',
            datefmt='%Y %m %d  %H:%M:%S',
            filename=os.path.join(self.__curDir,'apicloud.log'),
            filemode='a')
        sublime.status_message(u'开始真机同步')
        logging.debug('*'*30+'begin android sync'+'*'*30)
        logging.debug('sync dir is '+dirs[0])
        try:
            BeforeSystemRequests()
            self.load(dirs[0])
        except:
            logging.debug('run: exception happened as below')
            errMsg=traceback.format_exc()
            logging.debug(errMsg)
            sublime.error_message(u'真机同步出现异常')

        sublime.status_message(u'真机同步完成')
        logging.debug('*'*30+'android sync complete'+'*'*30)
        
    def checkBasicInfo(self):
        logging.debug('checkBasicInfo: current dir is '+self.__curDir)
        if not os.path.exists(os.path.join(self.__curDir,'tools')) or not os.path.isdir(os.path.join(self.__curDir,'tools')):
            logging.debug('checkBasicInfo:cannot find adb tools')
            return -1
        if not os.path.exists(os.path.join(self.__curDir,'appLoader','apicloud-loader','load.conf')) or not os.path.exists(os.path.join(self.__curDir,'appLoader','apicloud-loader','load.apk')):
            logging.debug('checkBasicInfo: cannot find appLoader')
            return -1
        import platform
        if 'darwin' in platform.system().lower() :
            self.__adbExe='"'+os.path.join(self.__curDir,'tools','adb')+'"'    
        elif 'windows' in platform.system().lower():                
            self.__adbExe='"'+os.path.join(self.__curDir,'tools','adb.exe')+'"'
        elif 'linux' in platform.system().lower():                
            self.__adbExe='"'+os.path.join('/usr/bin/','adb')+'"'
        else:
            logging.debug('checkBasicInfo: the platform is not support')
            sublime.error_message(u'checkBasicInfo: the platform is not support '+os.path.join('/usr/bin/','adb'))
            return -1
        logging.debug("checkBasicInfo: adbCmd is "+self.__adbExe)
        with open(os.path.join(self.__curDir,'appLoader','apicloud-loader','load.conf')) as f:
            config=json.load(f)
            logging.debug('checkBasicInfo: config content is '+str(config))
            if 'version' in config:
                self.__pendingVersion=config['version']
            if 'cmdLogType' in config:
                self.__cmdLogType=config['cmdLogType']
            if 'ignore' in config:
                self.__ignore=config['ignore']
        return 0

    def getDeviceListCmd(self):
        logging.debug('begin getDeviceListCmd')
        sublime.status_message(u'获得设备列表')
        cmd=self.__adbExe+' devices'
        logging.debug('getDeviceListCmd: cmd is '+cmd)
        output=os.popen(cmd)
        deviceList=[]
        lines=output.readlines()
        for line in lines:
            if 'List of devices attached' not in line:
                if 'device' in line:
                    deviceList.append(line.split('\tdevice')[0].strip())
        logging.debug('getDeviceListCmd: output is \n'+(''.join(lines)))
        logging.debug('getDeviceListCmd: deviceList is '+str(deviceList))
        return deviceList

    def getAppId(self, srcPath):
        logging.debug('begin getAppId: srcPath is '+srcPath)
        appId=-1
        if not os.path.exists(srcPath) or not os.path.isdir(srcPath):
            logging.debug('getAppId:file no exist or not a folder!')
            return appId
        appFileList=os.listdir(srcPath)
        if 'config.xml' not in appFileList:
            logging.debug('getAppId: please make sure sync the correct folder!')
            return -1
        with open(os.path.join(srcPath,"config.xml"),encoding='utf-8') as f:
            fileContent=f.read()
            r=re.compile(r"widget.*id.*=.*(A[0-9]{13})\"")
            searchResList=r.findall(fileContent)  
        if len(searchResList)>0:
            appId=searchResList[0]
        logging.debug('getAppId: appId is '+appId)
        return appId

    def getLoaderType(self,appId):
        logging.debug('begin getLoaderType')
        appIdPath=os.path.join(self.__curDir,'appLoader','custom-loader',appId)
        logging.debug('getLoaderType: appIdPath is '+os.path.join(appIdPath,'load.conf'))
        
        if os.path.exists(os.path.join(appIdPath,'load.conf')) and os.path.exists(os.path.join(appIdPath,'load.apk')):
            logging.debug('getLoaderType: It is may a customerized loader.')
            with open(os.path.join(appIdPath,'load.conf')) as f:
                config=json.load(f)
                logging.debug('getLoaderType: load.conf content is '+str(config))
                if 'version' in config:
                    version=config['version'].strip()
                if 'packageName' in config:
                    pkgName=config['packageName'].strip()

                if len(version)>0 and len(pkgName)>0:
                    self.__pendingVersion=version
                    self.__pkgName=pkgName
                    self.__loaderName='custom-loader'+os.path.sep+appId
                logging.debug('getLoaderType: pendingVerion is '+self.__pendingVersion)
                logging.debug('getLoaderType: pkgName is '+self.__pkgName)
        else:
            self.__pkgName='com.apicloud.apploader'
            self.__loaderName='apicloud-loader'    
            logging.debug('getLoaderType: path not exiest, will use default appLoader') 
        pass

    def pushDirOrFileCmd(self, serialNumber, srcPath, appId):
        fulldirname=os.path.abspath(srcPath)  
        tmpPathName='tmp-apicloud-folder'
        tmpPath=os.path.join(os.path.dirname(srcPath),tmpPathName)
        # force delete .git which is read only
        for (p,d,f) in os.walk(tmpPath):  
            if p.find('.git')>0:  
                if 'windows' in platform.system().lower():
                    os.popen('rd /s /q %s'%p) 
                elif 'darwin' in platform.system().lower():
                    os.popen('rm -rf %s'%p)
                elif 'linux' in platform.system().lower():
                    os.popen('rm -rf %s'%p)      
        if os.path.exists(tmpPath):
            self.CleanDir(tmpPath)
            os.rmdir(tmpPath)

        shutil.copytree(srcPath,tmpPath,ignore = shutil.ignore_patterns(*self.__ignore))
        logging.debug('begin pushDirOrFileCmd from '+srcPath+' for appId '+appId)
        sublime.status_message(u'开始推送widget包')
        desPath='/sdcard/UZMap/wgt/'+appId
        pushCmd=self.__adbExe+' -s '+serialNumber+' push "'+tmpPath+'" '+desPath
        logging.debug('pushDirOrFileCmd: pushCmd is '+pushCmd)
        (rtnCode,stdout,stderr)=runShellCommand(pushCmd,self.__cmdLogType)
        outputMsg=stdout+stderr
        logging.debug('pushDirOrFileCmd: outputMsg is '+outputMsg)    
        if 'error: device not found' in outputMsg:
            logging.debug('pushDirOrFileCmd: failed to run pushDirOrFileCmd')
            return False
        self.CleanDir(tmpPath)
        os.rmdir(tmpPath)
        logging.debug('pushDirOrFileCmd: pushDirOrFileCmd success!')
        return True
        
    def CleanDir(self, Dir):
        if os.path.isdir( Dir ):
            paths = os.listdir( Dir )
            for path in paths:
                filePath = os.path.join( Dir, path )
                if os.path.isfile( filePath ):
                    try:
                        os.remove( filePath )
                    except os.error:
                        autoRun.exception( "remove %s error." %filePath )
                elif os.path.isdir( filePath ):
                    shutil.rmtree(filePath,True)
        return True

    def pushStartInfo(self, serialNumber, appId):
        logging.debug('begin pushStartInfo for appId '+appId)
        sublime.status_message(u'开始推送启动文件')
        desPath='/sdcard/UZMap/A6965066952332/'
        srcPath=os.path.join(self.__curDir,'appLoader','startInfo.txt')
        with open(srcPath,"w") as file:
            file.write(appId)
        srcPath='"'+srcPath+'"'
        logging.debug('pushStartInfo: srcPath is '+srcPath+'startInfo.txt')
        pushCmd=self.__adbExe+' -s '+serialNumber+' push '+srcPath+' '+desPath
        logging.debug('pushStartInfo: pushCmd is '+pushCmd)
        (rtnCode,stdout,stderr)=runShellCommand(pushCmd,self.__cmdLogType)
        outputMsg=stdout+stderr
        logging.debug('pushStartInfo: outputMsg is '+outputMsg)    
        if 'error: device not found' in outputMsg:
            logging.debug('pushStartInfo: failed to run pushStartInfo')
            return False
        logging.debug('pushStartInfo: pushStartInfo success!')
        return True

    def compareAppLoaderVer(self,deviceVersion,appLoaderVersion):
        logging.debug('begin compareAppLoaderVer '+deviceVersion+' '+appLoaderVersion)
        deviceVersionArray=deviceVersion.split('.')
        appLoaderVersionArray=appLoaderVersion.split('.')
        for i in range(3):
            if appLoaderVersionArray[i]>deviceVersionArray[i]:
                logging.debug('compareAppLoaderVer: need update appLoader.')
                return True
        logging.debug('compareAppLoaderVer: no need to update appLoader.')
        return False

    def getApploaderVersionCmd(self,serialNumber):
        logging.debug('begin getApploaderVersionCmd for device '+serialNumber)
        version=-1
        cmd=self.__adbExe+' -s '+serialNumber+' shell dumpsys package '+self.__pkgName
        logging.debug('getApploaderVersionCmd: cmd is '+cmd)
        output=os.popen(cmd)
        verserOutput=output.read()
        r=re.compile("versionName=([0-9]{1,}.[0-9]{1,}.[0-9]{1,})")
        versionList=r.findall(verserOutput)
        if len(versionList)>0:
            version=versionList[0]
        return version

    def installAppLoaderCmd(self, serialNumber):
        logging.debug('begin installAppLoaderCmd')
        sublime.status_message(u'开始安装loader')
        appLoader='"'+os.path.join(self.__curDir,'appLoader',self.__loaderName,'load.apk')+'"'
        installCmd=self.__adbExe+' -s '+serialNumber+' install '+appLoader
        logging.debug('installAppLoaderCmd: cmd is '+installCmd)

        (rtnCode,stdout,stderr)=runShellCommand(installCmd,self.__cmdLogType)
        outputMsg=stdout+stderr
        logging.debug('installCmd: outputMsg is '+outputMsg)    
        if len(outputMsg)>0 and 'Success' not in outputMsg:
            logging.debug('installAppLoaderCmd: failed to run installAppLoader!')
            return False
        elif 'logFile'!=self.__cmdLogType:
            if -1==self.getApploaderVersionCmd(serialNumber):
                logging.debug('installAppLoaderCmd: failed to run installAppLoader!')
                return False

        logging.debug('installAppLoaderCmd: installAppLoader success!')
        return True

    def startApploaderCmd(self, serialNumber):
        logging.debug('begin startApploaderCmd for device '+serialNumber)
        sublime.status_message(u'正在启动loader')
        appLoaderPkg=self.__pkgName+'/com.uzmap.pkg.EntranceActivity'
        logging.debug('startApploaderCmd: pkg name is '+appLoaderPkg)
        startCmd=self.__adbExe +' -s '+serialNumber+' shell am start -W -n '+appLoaderPkg
        logging.debug('startApploaderCmd: cmd is '+startCmd)
        (rtnCode,stdout,stderr)=runShellCommand(startCmd,self.__cmdLogType)
        outputMsg=stdout+stderr
        logging.debug('startApploaderCmd: outputMsg is '+outputMsg)
        if 'error' in outputMsg:
            logging.debug('startApploaderCmd: failed to run startApploaderCmd!')
            return False
        logging.debug('startApploaderCmd: startApploaderCmd success!')
        return True

    def stopApploaderCmd(self, serialNumber):
        logging.debug('begin stopApploaderCmd for device '+serialNumber)
        sublime.status_message(u'停止设备上的loader')
        stopCmd=self.__adbExe +' -s '+serialNumber+' shell am force-stop '+self.__pkgName
        logging.debug('stopApploaderCmd: cmd is '+stopCmd)
        output=os.popen(stopCmd)
        logging.debug('stopApploaderCmd: stopApploaderCmd success!')
        pass

    def uninstallApploaderCmd(self, serialNumber):
        logging.debug('begin uninstallApploaderCmd for device '+serialNumber)
        sublime.status_message(u'正在卸载loader')
        uninstallCmd=self.__adbExe+' -s '+serialNumber+' uninstall '+self.__pkgName
        logging.debug(uninstallCmd)
        output=os.popen(uninstallCmd)
        uninstallOutput=str(output.read())
        logging.debug('uninstallApploaderCmd: output is '+uninstallOutput)
        if 'Success' not in uninstallOutput:
            logging.debug('uninstallApploaderCmd: failed to run uninstallApploaderCmd!')
            return False
        logging.debug('uninstallApploaderCmd: uninstallApploaderCmd finished!')
        return True

    def load(self,srcPath):
        isNeedInstall=False
        retVal=self.checkBasicInfo()
        if -1==retVal:
            logging.debug('load: failed to checkBasicInfo.')
            sublime.error_message(u'真机同步缺少文件')
            return
        deviceSerialList=self.getDeviceListCmd()
        if 0==len(deviceSerialList):
            logging.debug('load: no mobile device found on the computer.')
            sublime.error_message(u'未发现连接的设备')
            return
        appId=self.getAppId(srcPath)
        self.getLoaderType(appId)
        logging.debug('load: appId is '+ str(appId))
        if -1==appId:
            sublime.error_message(u'请确保目录正确')
            return 
        for serialNo in deviceSerialList:
            logging.debug('load: begin to sync machine '+serialNo)
            if not self.pushDirOrFileCmd(serialNo,srcPath,appId):
                sublime.error_message(u'向手机拷贝文件失败，请检查连接设备')
                return
            if self.__pkgName=='com.apicloud.apploader':
                if not self.pushStartInfo(serialNo,appId):
                    sublime.error_message(u'向手机拷贝启动文件失败，请检查连接设备')
                    return

            currentVersion=self.getApploaderVersionCmd(serialNo)
            if -1!=currentVersion :
                isNeedInstall=self.compareAppLoaderVer(currentVersion,self.__pendingVersion)                
            else:
                logging.debug('load: no appLoader found on the devices')
                isNeedInstall=True
            
            logging.debug('loader: the isNeedInstall flag is '+str(isNeedInstall))
            if isNeedInstall:
                if -1!=currentVersion:
                    if not self.uninstallApploaderCmd(serialNo):
                        logging.debug('load: failed to excute uninstallApploaderCmd')
                        sublime.error_message(u'卸载appLoader失败')
                        continue
                if not self.installAppLoaderCmd(serialNo):
                    logging.debug('load: failed to excute installAppLoaderCmd')
                    sublime.error_message(u'安装appLoader失败')
                    continue
            else:
                self.stopApploaderCmd(serialNo)
                import time
                time.sleep(1)

            if not self.startApploaderCmd(serialNo):
                sublime.error_message(u'真机同步启动appLoader失败')
                continue
        pass

class EnApicloudLoaderAndroidCommand(sublime_plugin.WindowCommand):
    """docstring for ApicloudLoaderAndroidCommand"""
    __adbExe='' 
    __curDir=''
    __pkgName='com.apicloud.apploader'
    __loaderName='apicloud-loader'
    __pendingVersion=''
    __cmdLogType='' #logFile
    __ignore=[".svn",".git"]
    def __init__(self,arg):
        self.__curDir=curDir
    
    def is_visible(self, dirs): 
        return len(dirs) > 0 and settings.get("envlang") == "en"

    def is_enabled(self, dirs):
        if 0==len(dirs):
            return False
        appFileList=os.listdir(dirs[0])
        if 'config.xml' in appFileList:
            return True
        return False

    def run(self, dirs):
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(message)s',
            datefmt='%Y %m %d  %H:%M:%S',
            filename=os.path.join(self.__curDir,'apicloud.log'),
            filemode='a')
        sublime.status_message(u'Starting synchronization with device')
        logging.debug('*'*30+'begin android sync'+'*'*30)
        logging.debug('sync dir is '+dirs[0])
        try:
            BeforeSystemRequests()
            self.load(dirs[0])
        except:
            logging.debug('run: exception happened as below')
            errMsg=traceback.format_exc()
            logging.debug(errMsg)
            sublime.error_message(u'Synchronization Failed!')

        sublime.status_message(u'Synchronization done!')
        logging.debug('*'*30+'android sync complete'+'*'*30)
        
    def checkBasicInfo(self):
        logging.debug('checkBasicInfo: current dir is '+self.__curDir)
        if not os.path.exists(os.path.join(self.__curDir,'tools')) or not os.path.isdir(os.path.join(self.__curDir,'tools')):
            logging.debug('checkBasicInfo:cannot find adb tools')
            return -1
        if not os.path.exists(os.path.join(self.__curDir,'appLoader','apicloud-loader','load.conf')) or not os.path.exists(os.path.join(self.__curDir,'appLoader','apicloud-loader','load.apk')):
            logging.debug('checkBasicInfo: cannot find appLoader')
            return -1
        import platform
        if 'darwin' in platform.system().lower() :
            self.__adbExe='"'+os.path.join(self.__curDir,'tools','adb')+'"'    
        elif 'windows' in platform.system().lower():                
            self.__adbExe='"'+os.path.join(self.__curDir,'tools','adb.exe')+'"'
        elif 'linux' in platform.system().lower():                
            self.__adbExe='"'+os.path.join('/usr/bin/','adb')+'"'
        else:
            logging.debug('checkBasicInfo: the platform is not support')
            sublime.error_message(u'checkBasicInfo: the platform is not support '+os.path.join('/usr/bin/','adb'))
            return -1
        logging.debug("checkBasicInfo: adbCmd is "+self.__adbExe)
        with open(os.path.join(self.__curDir,'appLoader','apicloud-loader','load.conf')) as f:
            config=json.load(f)
            logging.debug('checkBasicInfo: config content is '+str(config))
            if 'version' in config:
                self.__pendingVersion=config['version']
            if 'cmdLogType' in config:
                self.__cmdLogType=config['cmdLogType']
            if 'ignore' in config:
                self.__ignore=config['ignore']
        return 0

    def getDeviceListCmd(self):
        logging.debug('begin getDeviceListCmd')
        sublime.status_message(u'Getting list of devices')
        cmd=self.__adbExe+' devices'
        logging.debug('getDeviceListCmd: cmd is '+cmd)
        output=os.popen(cmd)
        deviceList=[]
        lines=output.readlines()
        for line in lines:
            if 'List of devices attached' not in line:
                if 'device' in line:
                    deviceList.append(line.split('\tdevice')[0].strip())
        logging.debug('getDeviceListCmd: output is \n'+(''.join(lines)))
        logging.debug('getDeviceListCmd: deviceList is '+str(deviceList))
        return deviceList

    def getAppId(self, srcPath):
        logging.debug('begin getAppId: srcPath is '+srcPath)
        appId=-1
        if not os.path.exists(srcPath) or not os.path.isdir(srcPath):
            logging.debug('getAppId:file no exist or not a folder!')
            return appId
        appFileList=os.listdir(srcPath)
        if 'config.xml' not in appFileList:
            logging.debug('getAppId: please make sure sync the correct folder!')
            return -1
        with open(os.path.join(srcPath,"config.xml"),encoding='utf-8') as f:
            fileContent=f.read()
            r=re.compile(r"widget.*id.*=.*(A[0-9]{13})\"")
            searchResList=r.findall(fileContent)  
        if len(searchResList)>0:
            appId=searchResList[0]
        logging.debug('getAppId: appId is '+appId)
        return appId

    def getLoaderType(self,appId):
        logging.debug('begin getLoaderType')
        appIdPath=os.path.join(self.__curDir,'appLoader','custom-loader',appId)
        logging.debug('getLoaderType: appIdPath is '+os.path.join(appIdPath,'load.conf'))
        
        if os.path.exists(os.path.join(appIdPath,'load.conf')) and os.path.exists(os.path.join(appIdPath,'load.apk')):
            logging.debug('getLoaderType: It is may a customerized loader.')
            with open(os.path.join(appIdPath,'load.conf')) as f:
                config=json.load(f)
                logging.debug('getLoaderType: load.conf content is '+str(config))
                if 'version' in config:
                    version=config['version'].strip()
                if 'packageName' in config:
                    pkgName=config['packageName'].strip()

                if len(version)>0 and len(pkgName)>0:
                    self.__pendingVersion=version
                    self.__pkgName=pkgName
                    self.__loaderName='custom-loader'+os.path.sep+appId
                logging.debug('getLoaderType: pendingVerion is '+self.__pendingVersion)
                logging.debug('getLoaderType: pkgName is '+self.__pkgName)
        else:
            self.__pkgName='com.apicloud.apploader'
            self.__loaderName='apicloud-loader'    
            logging.debug('getLoaderType: path not exiest, will use default appLoader') 
        pass

    def pushDirOrFileCmd(self, serialNumber, srcPath, appId):
        fulldirname=os.path.abspath(srcPath)  
        tmpPathName='tmp-apicloud-folder'
        tmpPath=os.path.join(os.path.dirname(srcPath),tmpPathName)
        # force delete .git which is read only
        for (p,d,f) in os.walk(tmpPath):  
            if p.find('.git')>0:  
                if 'windows' in platform.system().lower():
                    os.popen('rd /s /q %s'%p) 
                elif 'darwin' in platform.system().lower():
                    os.popen('rm -rf %s'%p)
                elif 'linux' in platform.system().lower():
                    os.popen('rm -rf %s'%p)      
        if os.path.exists(tmpPath):
            self.CleanDir(tmpPath)
            os.rmdir(tmpPath)

        shutil.copytree(srcPath,tmpPath,ignore = shutil.ignore_patterns(*self.__ignore))
        logging.debug('begin pushDirOrFileCmd from '+srcPath+' for appId '+appId)
        sublime.status_message(u'Begining push widget package')
        desPath='/sdcard/UZMap/wgt/'+appId
        pushCmd=self.__adbExe+' -s '+serialNumber+' push "'+tmpPath+'" '+desPath
        logging.debug('pushDirOrFileCmd: pushCmd is '+pushCmd)
        (rtnCode,stdout,stderr)=runShellCommand(pushCmd,self.__cmdLogType)
        outputMsg=stdout+stderr
        logging.debug('pushDirOrFileCmd: outputMsg is '+outputMsg)    
        if 'error: device not found' in outputMsg:
            logging.debug('pushDirOrFileCmd: failed to run pushDirOrFileCmd')
            return False
        self.CleanDir(tmpPath)
        os.rmdir(tmpPath)
        logging.debug('pushDirOrFileCmd: pushDirOrFileCmd success!')
        return True
        
    def CleanDir(self, Dir):
        if os.path.isdir( Dir ):
            paths = os.listdir( Dir )
            for path in paths:
                filePath = os.path.join( Dir, path )
                if os.path.isfile( filePath ):
                    try:
                        os.remove( filePath )
                    except os.error:
                        autoRun.exception( "remove %s error." %filePath )
                elif os.path.isdir( filePath ):
                    shutil.rmtree(filePath,True)
        return True

    def pushStartInfo(self, serialNumber, appId):
        logging.debug('begin pushStartInfo for appId '+appId)
        sublime.status_message(u'Begining push startup file')
        desPath='/sdcard/UZMap/A6965066952332/'
        srcPath=os.path.join(self.__curDir,'appLoader','startInfo.txt')
        with open(srcPath,"w") as file:
            file.write(appId)
        srcPath='"'+srcPath+'"'
        logging.debug('pushStartInfo: srcPath is '+srcPath+'startInfo.txt')
        pushCmd=self.__adbExe+' -s '+serialNumber+' push '+srcPath+' '+desPath
        logging.debug('pushStartInfo: pushCmd is '+pushCmd)
        (rtnCode,stdout,stderr)=runShellCommand(pushCmd,self.__cmdLogType)
        outputMsg=stdout+stderr
        logging.debug('pushStartInfo: outputMsg is '+outputMsg)    
        if 'error: device not found' in outputMsg:
            logging.debug('pushStartInfo: failed to run pushStartInfo')
            return False
        logging.debug('pushStartInfo: pushStartInfo success!')
        return True

    def compareAppLoaderVer(self,deviceVersion,appLoaderVersion):
        logging.debug('begin compareAppLoaderVer '+deviceVersion+' '+appLoaderVersion)
        deviceVersionArray=deviceVersion.split('.')
        appLoaderVersionArray=appLoaderVersion.split('.')
        for i in range(3):
            if appLoaderVersionArray[i]>deviceVersionArray[i]:
                logging.debug('compareAppLoaderVer: need update appLoader.')
                return True
        logging.debug('compareAppLoaderVer: no need to update appLoader.')
        return False

    def getApploaderVersionCmd(self,serialNumber):
        logging.debug('begin getApploaderVersionCmd for device '+serialNumber)
        version=-1
        cmd=self.__adbExe+' -s '+serialNumber+' shell dumpsys package '+self.__pkgName
        logging.debug('getApploaderVersionCmd: cmd is '+cmd)
        output=os.popen(cmd)
        verserOutput=output.read()
        r=re.compile("versionName=([0-9]{1,}.[0-9]{1,}.[0-9]{1,})")
        versionList=r.findall(verserOutput)
        if len(versionList)>0:
            version=versionList[0]
        return version

    def installAppLoaderCmd(self, serialNumber):
        logging.debug('begin installAppLoaderCmd')
        sublime.status_message(u'loader installation')
        appLoader='"'+os.path.join(self.__curDir,'appLoader',self.__loaderName,'load.apk')+'"'
        installCmd=self.__adbExe+' -s '+serialNumber+' install '+appLoader
        logging.debug('installAppLoaderCmd: cmd is '+installCmd)

        (rtnCode,stdout,stderr)=runShellCommand(installCmd,self.__cmdLogType)
        outputMsg=stdout+stderr
        logging.debug('installCmd: outputMsg is '+outputMsg)    
        if len(outputMsg)>0 and 'Success' not in outputMsg:
            logging.debug('installAppLoaderCmd: failed to run installAppLoader!')
            return False
        elif 'logFile'!=self.__cmdLogType:
            if -1==self.getApploaderVersionCmd(serialNumber):
                logging.debug('installAppLoaderCmd: failed to run installAppLoader!')
                return False

        logging.debug('installAppLoaderCmd: installAppLoader success!')
        return True

    def startApploaderCmd(self, serialNumber):
        logging.debug('begin startApploaderCmd for device '+serialNumber)
        sublime.status_message(u'Starting loader')
        appLoaderPkg=self.__pkgName+'/com.uzmap.pkg.EntranceActivity'
        logging.debug('startApploaderCmd: pkg name is '+appLoaderPkg)
        startCmd=self.__adbExe +' -s '+serialNumber+' shell am start -W -n '+appLoaderPkg
        logging.debug('startApploaderCmd: cmd is '+startCmd)
        (rtnCode,stdout,stderr)=runShellCommand(startCmd,self.__cmdLogType)
        outputMsg=stdout+stderr
        logging.debug('startApploaderCmd: outputMsg is '+outputMsg)
        if 'error' in outputMsg:
            logging.debug('startApploaderCmd: failed to run startApploaderCmd!')
            return False
        logging.debug('startApploaderCmd: startApploaderCmd success!')
        return True

    def stopApploaderCmd(self, serialNumber):
        logging.debug('begin stopApploaderCmd for device '+serialNumber)
        sublime.status_message(u'Stopping App loader')
        stopCmd=self.__adbExe +' -s '+serialNumber+' shell am force-stop '+self.__pkgName
        logging.debug('stopApploaderCmd: cmd is '+stopCmd)
        output=os.popen(stopCmd)
        logging.debug('stopApploaderCmd: stopApploaderCmd success!')
        pass

    def uninstallApploaderCmd(self, serialNumber):
        logging.debug('begin uninstallApploaderCmd for device '+serialNumber)
        sublime.status_message(u'Uninstalling app loader')
        uninstallCmd=self.__adbExe+' -s '+serialNumber+' uninstall '+self.__pkgName
        logging.debug(uninstallCmd)
        output=os.popen(uninstallCmd)
        uninstallOutput=str(output.read())
        logging.debug('uninstallApploaderCmd: output is '+uninstallOutput)
        if 'Success' not in uninstallOutput:
            logging.debug('uninstallApploaderCmd: failed to run uninstallApploaderCmd!')
            return False
        logging.debug('uninstallApploaderCmd: uninstallApploaderCmd finished!')
        return True

    def load(self,srcPath):
        isNeedInstall=False
        retVal=self.checkBasicInfo()
        if -1==retVal:
            logging.debug('load: failed to checkBasicInfo.')
            sublime.error_message(u'Failure reason: missing files')
            return
        deviceSerialList=self.getDeviceListCmd()
        if 0==len(deviceSerialList):
            logging.debug('load: no mobile device found on the computer.')
            sublime.error_message(u'No connected device')
            return
        appId=self.getAppId(srcPath)
        self.getLoaderType(appId)
        logging.debug('load: appId is '+ str(appId))
        if -1==appId:
            sublime.error_message(u'Make sure the folder is correct')
            return 
        for serialNo in deviceSerialList:
            logging.debug('load: begin to sync machine '+serialNo)
            if not self.pushDirOrFileCmd(serialNo,srcPath,appId):
                sublime.error_message(u'File copy to your phone fails, check the connection device')
                return
            if self.__pkgName=='com.apicloud.apploader':
                if not self.pushStartInfo(serialNo,appId):
                    sublime.error_message(u'File copied to your phone fails to start, check the connection device')
                    return

            currentVersion=self.getApploaderVersionCmd(serialNo)
            if -1!=currentVersion :
                isNeedInstall=self.compareAppLoaderVer(currentVersion,self.__pendingVersion)                
            else:
                logging.debug('load: no appLoader found on the devices')
                isNeedInstall=True
            
            logging.debug('loader: the isNeedInstall flag is '+str(isNeedInstall))
            if isNeedInstall:
                if -1!=currentVersion:
                    if not self.uninstallApploaderCmd(serialNo):
                        logging.debug('load: failed to excute uninstallApploaderCmd')
                        sublime.error_message(u'Uninstall app Loader failed')
                        continue
                if not self.installAppLoaderCmd(serialNo):
                    logging.debug('load: failed to excute installAppLoaderCmd')
                    sublime.error_message(u'Install app Loader failed')
                    continue
            else:
                self.stopApploaderCmd(serialNo)
                import time
                time.sleep(1)

            if not self.startApploaderCmd(serialNo):
                sublime.error_message(u'Apploader start failed')
                continue
        pass

class FrApicloudLoaderAndroidCommand(sublime_plugin.WindowCommand):
    """docstring for ApicloudLoaderAndroidCommand"""
    __adbExe='' 
    __curDir=''
    __pkgName='com.apicloud.apploader'
    __loaderName='apicloud-loader'
    __pendingVersion=''
    __cmdLogType='' #logFile
    __ignore=[".svn",".git"]
    def __init__(self,arg):
        self.__curDir=curDir
    
    def is_visible(self, dirs): 
        return len(dirs) > 0 and settings.get("envlang") == "fr"

    def is_enabled(self, dirs):
        if 0==len(dirs):
            return False
        appFileList=os.listdir(dirs[0])
        if 'config.xml' in appFileList:
            return True
        return False

    def run(self, dirs):
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(message)s',
            datefmt='%Y %m %d  %H:%M:%S',
            filename=os.path.join(self.__curDir,'apicloud.log'),
            filemode='a')
        sublime.status_message(u'Demarrage de la synchronisation')
        logging.debug('*'*30+'begin android sync'+'*'*30)
        logging.debug('sync dir is '+dirs[0])
        try:
            BeforeSystemRequests()
            self.load(dirs[0])
        except:
            logging.debug('run: exception happened as below')
            errMsg=traceback.format_exc()
            logging.debug(errMsg)
            sublime.error_message(u'Echec de la synchronisation')

        sublime.status_message(u'Synchronisation achevee avec succes')
        logging.debug('*'*30+'android sync complete'+'*'*30)
        
    def checkBasicInfo(self):
        logging.debug('checkBasicInfo: current dir is '+self.__curDir)
        if not os.path.exists(os.path.join(self.__curDir,'tools')) or not os.path.isdir(os.path.join(self.__curDir,'tools')):
            logging.debug('checkBasicInfo:cannot find adb tools')
            return -1
        if not os.path.exists(os.path.join(self.__curDir,'appLoader','apicloud-loader','load.conf')) or not os.path.exists(os.path.join(self.__curDir,'appLoader','apicloud-loader','load.apk')):
            logging.debug('checkBasicInfo: cannot find appLoader')
            return -1
        import platform
        if 'darwin' in platform.system().lower() :
            self.__adbExe='"'+os.path.join(self.__curDir,'tools','adb')+'"'    
        elif 'windows' in platform.system().lower():                
            self.__adbExe='"'+os.path.join(self.__curDir,'tools','adb.exe')+'"'
        elif 'linux' in platform.system().lower():                
            self.__adbExe='"'+os.path.join('/usr/bin/','adb')+'"'
        else:
            logging.debug('checkBasicInfo: the platform is not support')
            sublime.error_message(u'checkBasicInfo: the platform is not support '+os.path.join('/usr/bin/','adb'))
            return -1
        logging.debug("checkBasicInfo: adbCmd is "+self.__adbExe)
        with open(os.path.join(self.__curDir,'appLoader','apicloud-loader','load.conf')) as f:
            config=json.load(f)
            logging.debug('checkBasicInfo: config content is '+str(config))
            if 'version' in config:
                self.__pendingVersion=config['version']
            if 'cmdLogType' in config:
                self.__cmdLogType=config['cmdLogType']
            if 'ignore' in config:
                self.__ignore=config['ignore']
        return 0

    def getDeviceListCmd(self):
        logging.debug('begin getDeviceListCmd')
        sublime.status_message(u'Liste des terminaux')
        cmd=self.__adbExe+' devices'
        logging.debug('getDeviceListCmd: cmd is '+cmd)
        output=os.popen(cmd)
        deviceList=[]
        lines=output.readlines()
        for line in lines:
            if 'List of devices attached' not in line:
                if 'device' in line:
                    deviceList.append(line.split('\tdevice')[0].strip())
        logging.debug('getDeviceListCmd: output is \n'+(''.join(lines)))
        logging.debug('getDeviceListCmd: deviceList is '+str(deviceList))
        return deviceList

    def getAppId(self, srcPath):
        logging.debug('begin getAppId: srcPath is '+srcPath)
        appId=-1
        if not os.path.exists(srcPath) or not os.path.isdir(srcPath):
            logging.debug('getAppId:file no exist or not a folder!')
            return appId
        appFileList=os.listdir(srcPath)
        if 'config.xml' not in appFileList:
            logging.debug('getAppId: please make sure sync the correct folder!')
            return -1
        with open(os.path.join(srcPath,"config.xml"),encoding='utf-8') as f:
            fileContent=f.read()
            r=re.compile(r"widget.*id.*=.*(A[0-9]{13})\"")
            searchResList=r.findall(fileContent)  
        if len(searchResList)>0:
            appId=searchResList[0]
        logging.debug('getAppId: appId is '+appId)
        return appId

    def getLoaderType(self,appId):
        logging.debug('begin getLoaderType')
        appIdPath=os.path.join(self.__curDir,'appLoader','custom-loader',appId)
        logging.debug('getLoaderType: appIdPath is '+os.path.join(appIdPath,'load.conf'))
        
        if os.path.exists(os.path.join(appIdPath,'load.conf')) and os.path.exists(os.path.join(appIdPath,'load.apk')):
            logging.debug('getLoaderType: It is may a customerized loader.')
            with open(os.path.join(appIdPath,'load.conf')) as f:
                config=json.load(f)
                logging.debug('getLoaderType: load.conf content is '+str(config))
                if 'version' in config:
                    version=config['version'].strip()
                if 'packageName' in config:
                    pkgName=config['packageName'].strip()

                if len(version)>0 and len(pkgName)>0:
                    self.__pendingVersion=version
                    self.__pkgName=pkgName
                    self.__loaderName='custom-loader'+os.path.sep+appId
                logging.debug('getLoaderType: pendingVerion is '+self.__pendingVersion)
                logging.debug('getLoaderType: pkgName is '+self.__pkgName)
        else:
            self.__pkgName='com.apicloud.apploader'
            self.__loaderName='apicloud-loader'    
            logging.debug('getLoaderType: path not exiest, will use default appLoader') 
        pass

    def pushDirOrFileCmd(self, serialNumber, srcPath, appId):
        fulldirname=os.path.abspath(srcPath)  
        tmpPathName='tmp-apicloud-folder'
        tmpPath=os.path.join(os.path.dirname(srcPath),tmpPathName)
        # force delete .git which is read only
        for (p,d,f) in os.walk(tmpPath):  
            if p.find('.git')>0:  
                if 'windows' in platform.system().lower():
                    os.popen('rd /s /q %s'%p) 
                elif 'darwin' in platform.system().lower():
                    os.popen('rm -rf %s'%p)
                elif 'linux' in platform.system().lower():
                    os.popen('rm -rf %s'%p)      
        if os.path.exists(tmpPath):
            self.CleanDir(tmpPath)
            os.rmdir(tmpPath)

        shutil.copytree(srcPath,tmpPath,ignore = shutil.ignore_patterns(*self.__ignore))
        logging.debug('begin pushDirOrFileCmd from '+srcPath+' for appId '+appId)
        sublime.status_message(u'Execution "Push Widget"')
        desPath='/sdcard/UZMap/wgt/'+appId
        pushCmd=self.__adbExe+' -s '+serialNumber+' push "'+tmpPath+'" '+desPath
        logging.debug('pushDirOrFileCmd: pushCmd is '+pushCmd)
        (rtnCode,stdout,stderr)=runShellCommand(pushCmd,self.__cmdLogType)
        outputMsg=stdout+stderr
        logging.debug('pushDirOrFileCmd: outputMsg is '+outputMsg)    
        if 'error: device not found' in outputMsg:
            logging.debug('pushDirOrFileCmd: failed to run pushDirOrFileCmd')
            return False
        self.CleanDir(tmpPath)
        os.rmdir(tmpPath)
        logging.debug('pushDirOrFileCmd: pushDirOrFileCmd success!')
        return True
        
    def CleanDir(self, Dir):
        if os.path.isdir( Dir ):
            paths = os.listdir( Dir )
            for path in paths:
                filePath = os.path.join( Dir, path )
                if os.path.isfile( filePath ):
                    try:
                        os.remove( filePath )
                    except os.error:
                        autoRun.exception( "remove %s error." %filePath )
                elif os.path.isdir( filePath ):
                    shutil.rmtree(filePath,True)
        return True

    def pushStartInfo(self, serialNumber, appId):
        logging.debug('begin pushStartInfo for appId '+appId)
        sublime.status_message(u'Execution "Push" du fichier de demarrage')
        desPath='/sdcard/UZMap/A6965066952332/'
        srcPath=os.path.join(self.__curDir,'appLoader','startInfo.txt')
        with open(srcPath,"w") as file:
            file.write(appId)
        srcPath='"'+srcPath+'"'
        logging.debug('pushStartInfo: srcPath is '+srcPath+'startInfo.txt')
        pushCmd=self.__adbExe+' -s '+serialNumber+' push '+srcPath+' '+desPath
        logging.debug('pushStartInfo: pushCmd is '+pushCmd)
        (rtnCode,stdout,stderr)=runShellCommand(pushCmd,self.__cmdLogType)
        outputMsg=stdout+stderr
        logging.debug('pushStartInfo: outputMsg is '+outputMsg)    
        if 'error: device not found' in outputMsg:
            logging.debug('pushStartInfo: failed to run pushStartInfo')
            return False
        logging.debug('pushStartInfo: pushStartInfo success!')
        return True

    def compareAppLoaderVer(self,deviceVersion,appLoaderVersion):
        logging.debug('begin compareAppLoaderVer '+deviceVersion+' '+appLoaderVersion)
        deviceVersionArray=deviceVersion.split('.')
        appLoaderVersionArray=appLoaderVersion.split('.')
        for i in range(3):
            if appLoaderVersionArray[i]>deviceVersionArray[i]:
                logging.debug('compareAppLoaderVer: need update appLoader.')
                return True
        logging.debug('compareAppLoaderVer: no need to update appLoader.')
        return False

    def getApploaderVersionCmd(self,serialNumber):
        logging.debug('begin getApploaderVersionCmd for device '+serialNumber)
        version=-1
        cmd=self.__adbExe+' -s '+serialNumber+' shell dumpsys package '+self.__pkgName
        logging.debug('getApploaderVersionCmd: cmd is '+cmd)
        output=os.popen(cmd)
        verserOutput=output.read()
        r=re.compile("versionName=([0-9]{1,}.[0-9]{1,}.[0-9]{1,})")
        versionList=r.findall(verserOutput)
        if len(versionList)>0:
            version=versionList[0]
        return version

    def installAppLoaderCmd(self, serialNumber):
        logging.debug('begin installAppLoaderCmd')
        sublime.status_message(u'Installation du "loader"')
        appLoader='"'+os.path.join(self.__curDir,'appLoader',self.__loaderName,'load.apk')+'"'
        installCmd=self.__adbExe+' -s '+serialNumber+' install '+appLoader
        logging.debug('installAppLoaderCmd: cmd is '+installCmd)

        (rtnCode,stdout,stderr)=runShellCommand(installCmd,self.__cmdLogType)
        outputMsg=stdout+stderr
        logging.debug('installCmd: outputMsg is '+outputMsg)    
        if len(outputMsg)>0 and 'Success' not in outputMsg:
            logging.debug('installAppLoaderCmd: failed to run installAppLoader!')
            return False
        elif 'logFile'!=self.__cmdLogType:
            if -1==self.getApploaderVersionCmd(serialNumber):
                logging.debug('installAppLoaderCmd: failed to run installAppLoader!')
                return False

        logging.debug('installAppLoaderCmd: installAppLoader success!')
        return True

    def startApploaderCmd(self, serialNumber):
        logging.debug('begin startApploaderCmd for device '+serialNumber)
        sublime.status_message(u'Lancement du "loader"')
        appLoaderPkg=self.__pkgName+'/com.uzmap.pkg.EntranceActivity'
        logging.debug('startApploaderCmd: pkg name is '+appLoaderPkg)
        startCmd=self.__adbExe +' -s '+serialNumber+' shell am start -W -n '+appLoaderPkg
        logging.debug('startApploaderCmd: cmd is '+startCmd)
        (rtnCode,stdout,stderr)=runShellCommand(startCmd,self.__cmdLogType)
        outputMsg=stdout+stderr
        logging.debug('startApploaderCmd: outputMsg is '+outputMsg)
        if 'error' in outputMsg:
            logging.debug('startApploaderCmd: failed to run startApploaderCmd!')
            return False
        logging.debug('startApploaderCmd: startApploaderCmd success!')
        return True

    def stopApploaderCmd(self, serialNumber):
        logging.debug('begin stopApploaderCmd for device '+serialNumber)
        sublime.status_message(u'Arret du "loader"')
        stopCmd=self.__adbExe +' -s '+serialNumber+' shell am force-stop '+self.__pkgName
        logging.debug('stopApploaderCmd: cmd is '+stopCmd)
        output=os.popen(stopCmd)
        logging.debug('stopApploaderCmd: stopApploaderCmd success!')
        pass

    def uninstallApploaderCmd(self, serialNumber):
        logging.debug('begin uninstallApploaderCmd for device '+serialNumber)
        sublime.status_message(u'Desinstallation du "loader"')
        uninstallCmd=self.__adbExe+' -s '+serialNumber+' uninstall '+self.__pkgName
        logging.debug(uninstallCmd)
        output=os.popen(uninstallCmd)
        uninstallOutput=str(output.read())
        logging.debug('uninstallApploaderCmd: output is '+uninstallOutput)
        if 'Success' not in uninstallOutput:
            logging.debug('uninstallApploaderCmd: failed to run uninstallApploaderCmd!')
            return False
        logging.debug('uninstallApploaderCmd: uninstallApploaderCmd finished!')
        return True

    def load(self,srcPath):
        isNeedInstall=False
        retVal=self.checkBasicInfo()
        if -1==retVal:
            logging.debug('load: failed to checkBasicInfo.')
            sublime.error_message(u'Echec de la synchronisation: fichiers manquants')
            return
        deviceSerialList=self.getDeviceListCmd()
        if 0==len(deviceSerialList):
            logging.debug('load: no mobile device found on the computer.')
            sublime.error_message(u'Aucun terminal connectE n''a ete trouvE')
            return
        appId=self.getAppId(srcPath)
        self.getLoaderType(appId)
        logging.debug('load: appId is '+ str(appId))
        if -1==appId:
            sublime.error_message(u'Assurez vous que le repertoire est le bon')
            return 
        for serialNo in deviceSerialList:
            logging.debug('load: begin to sync machine '+serialNo)
            if not self.pushDirOrFileCmd(serialNo,srcPath,appId):
                sublime.error_message(u'Echec de la copie du fichie vers le terminal, verifiez la connexion')
                return
            if self.__pkgName=='com.apicloud.apploader':
                if not self.pushStartInfo(serialNo,appId):
                    sublime.error_message(u'Echec de l''execution de la copie, verifiez la connexion')
                    return

            currentVersion=self.getApploaderVersionCmd(serialNo)
            if -1!=currentVersion :
                isNeedInstall=self.compareAppLoaderVer(currentVersion,self.__pendingVersion)                
            else:
                logging.debug('load: no appLoader found on the devices')
                isNeedInstall=True
            
            logging.debug('loader: the isNeedInstall flag is '+str(isNeedInstall))
            if isNeedInstall:
                if -1!=currentVersion:
                    if not self.uninstallApploaderCmd(serialNo):
                        logging.debug('load: failed to excute uninstallApploaderCmd')
                        sublime.error_message(u'Echec de la desinstallation du "loader"')
                        continue
                if not self.installAppLoaderCmd(serialNo):
                    logging.debug('load: failed to excute installAppLoaderCmd')
                    sublime.error_message(u'Echec de l''installation du "loader"')
                    continue
            else:
                self.stopApploaderCmd(serialNo)
                import time
                time.sleep(1)

            if not self.startApploaderCmd(serialNo):
                sublime.error_message(u'Echec du lancement du "loader"')
                continue
        pass


##############################################################################################

class ApicloudLoaderIosKeyCommand(sublime_plugin.TextCommand):
    """docstring for ApicloudLoaderIosKeyCommand"""

    def run(self, edit):
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(message)s',
            datefmt='%Y %m %d  %H:%M:%S',
            filename=os.path.join(curDir,'apicloud.log'),
            filemode='a')
        if settings.get("envlang") == "en":
            sublime.status_message(u'IOS Device Sync failed')
        elif settings.get("envlang") == "fr": 
           sublime.status_message(u'Echec de la syncrhonisation avec le terminal IOS')
        else:
            sublime.status_message(u'开始IOS真机同步')      
        logging.debug('*'*30+'begin ios key sync'+'*'*30)

        file_name=self.view.file_name()
        syncPath=getWidgetPath(file_name)
        if len(syncPath) > 0:
            logging.debug('key sync dir is '+syncPath)
            try:
                BeforeSystemRequests()
                loader = ApicloudLoaderIosCommand('')
                loader.loadIos(syncPath)
            except:
                logging.debug('run: exception happened as below')
                errMsg=traceback.format_exc()
                logging.debug(errMsg)
                print(errMsg)
                if settings.get("envlang") == "en":
                    sublime.error_message(u'IOS Sync abnormal')
                elif settings.get("envlang") == "fr":
                    sublime.error_message(u'Synchronisation IOS anormal')
                else:
                    sublime.error_message(u'IOS真机同步出现异常')    
            
            if settings.get("envlang") == "en":
                sublime.status_message(u'IOS Sync done!')
            elif settings.get("envlang") == "fr":
                sublime.status_message(u'Synchronisation IOS finie avec succes')
            else:
                sublime.status_message(u'IOS真机同步完成')

            logging.debug('*'*30+'ios key sync complete'+'*'*30)
        else:
            if settings.get("envlang") == "en":
                sublime.error_message(u'Please make sure that the current file is in the correct directory')
            elif settings.get("envlang") == "fr":
                sublime.error_message(u'Veuillez vous assurer que le fichier courant est dans le bon repertoire')
            else:
                sublime.error_message(u'请确保当前文件所在目录正确')
        return

class ApicloudLoaderIosCommand(sublime_plugin.WindowCommand):
    """docstring for ApicloudIOSLoaderCommand"""
    __adbExe='' 
    __curDir=''
    __pkgName='com.apicloud.apploader'
    __loaderName='apicloud-loader'
    __cmdLogType='' #logFile
    __ignore=['.svn','.git']

    def __init__(self,arg):
        self.__curDir=curDir
    
    def is_visible(self, dirs): 
        return len(dirs) > 0 and not (settings.get("envlang") == "en" or settings.get("envlang") == "fr")

    def is_enabled(self, dirs):
        if 0==len(dirs):
            return False
        appFileList=os.listdir(dirs[0])
        if 'config.xml' in appFileList:
            return True
        return False

    def run(self, dirs):
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(message)s',
            datefmt='%Y %m %d  %H:%M:%S',
            filename=os.path.join(self.__curDir,'apicloud.log'),
            filemode='a')
        sublime.status_message(u'IOS开始真机同步')
        logging.debug('*'*30+'begin ios sync'+'*'*30)
        logging.debug('sync dir is '+dirs[0])
        try:
            BeforeSystemRequests()
            self.loadIos(dirs[0])
        except:
            logging.debug('run: exception happened as below')
            errMsg=traceback.format_exc()
            logging.debug(errMsg)
            print(errMsg)
            sublime.error_message(u'IOS真机同步出现异常')

        sublime.status_message(u'真机同步完成')
        logging.debug('*'*30+'ios sync complete'+'*'*30)

    def CleanDir(self, Dir):
        if os.path.isdir( Dir ):
            paths = os.listdir( Dir )
            for path in paths:
                filePath = os.path.join( Dir, path )
                if os.path.isfile( filePath ):
                    try:
                        os.remove( filePath )
                    except os.error:
                        autoRun.exception( "remove %s error." %filePath )
                elif os.path.isdir( filePath ):
                    shutil.rmtree(filePath,True)
        return True        

    def loadIos(self, srcPath):
        logging.debug('loadIos: current dir is ')
        if 'windows' in platform.system().lower():
            if not os.path.exists(os.path.join(self.__curDir,'tools','jre','bin')) :
                logging.debug('loadIos: cannot find load.conf')
                sublime.error_message(u'缺少JRE环境')
                return
        else: 
            (rtnCode,stdout,stderr)=runShellCommand('java -version',self.__cmdLogType)
            outputMsg=stdout+stderr
            if 'version' not in outputMsg:
                sublime.error_message(u'缺少JRE环境')
                return
        if not os.path.exists(os.path.join(self.__curDir,'appLoader','apicloud-loader-ios','load.conf')) or not os.path.exists(os.path.join(self.__curDir,'appLoader','apicloud-loader','load.apk')):
            logging.debug('loadIos: cannot find load.conf')
            sublime.error_message(u'真机同步缺少文件')
            return
        appId=self.getAppId(srcPath)
        self.getIosLoaderType(appId)
        logging.debug('loadIos: appId is '+ str(appId))
        if -1==appId:
            sublime.error_message(u'请确保目录正确')
            return

        if 'windows' in platform.system().lower():
            javaCmd=os.path.join(self.__curDir,'tools','jre','bin','java')
        else:
            javaCmd='java'

        fulldirname=os.path.abspath(srcPath)  
        tmpPathName='tmp-apicloud-folder'
        tmpPath=os.path.join(os.path.dirname(srcPath),tmpPathName)
        # force delete .git which is read only
        for (p,d,f) in os.walk(tmpPath):  
            if p.find('.git')>0:  
                if 'windows' in platform.system().lower():
                    os.popen('rd /s /q %s'%p) 
                elif 'darwin' in platform.system().lower():
                    os.popen('rm -rf %s'%p)
                elif 'linux' in platform.system().lower():
                    os.popen('rm -rf %s'%p)     
        if os.path.exists(tmpPath):
            self.CleanDir(tmpPath)
            os.rmdir(tmpPath)
        shutil.copytree(srcPath,tmpPath,ignore = shutil.ignore_patterns(*self.__ignore))

        jarFile=os.path.join(self.__curDir,'tools','syncapp.jar')
        iosLoaderPath=os.path.join(self.__curDir,'appLoader',self.__loaderName)
        versionFile=os.path.join(iosLoaderPath,'load.conf')
        iosLoaderFile=os.path.join(iosLoaderPath,'load.ipa')

        iosSyncCmd='"'+javaCmd+'" -jar "'+jarFile+'" "'+srcPath+'" "'+iosLoaderPath+'" "'+iosLoaderFile+'" "'+versionFile+'"'
        logging.debug('loadIos: cmd is'+iosSyncCmd)
        (rtnCode,stdout,stderr)=runShellCommand(iosSyncCmd,self.__cmdLogType)
        outputMsg=stdout+stderr
        logging.debug('loadIos: outputMsg is '+outputMsg)
        self.CleanDir(tmpPath)
        os.rmdir(tmpPath)
        
        if 'No iOS device attached' in outputMsg:
            sublime.error_message(u'未发现连接的设备')
            logging.debug('loadIos: no ios device found !')
        elif 'error' in outputMsg or 'failed' in outputMsg:
            logging.debug('loadIos: failed to sync ios')
            sublime.error_message(u'IOS真机同步失败')
        else:
            logging.debug('loadIos: ios sync success.')
            sublime.message_dialog(u'IOS真机同步完成')

    def getAppId(self, srcPath):
        logging.debug('begin getAppId: srcPath is '+srcPath)
        appId=-1
        if not os.path.exists(srcPath) or not os.path.isdir(srcPath):
            logging.debug('getAppId:file no exist or not a folder!')
            return appId
        appFileList=os.listdir(srcPath)
        if 'config.xml' not in appFileList:
            logging.debug('getAppId: please make sure sync the correct folder!')
            return -1
        with open(os.path.join(srcPath,"config.xml"),encoding='utf-8') as f:
            fileContent=f.read()
            r=re.compile(r"widget.*id.*=.*(A[0-9]{13})\"")
            searchResList=r.findall(fileContent)  
        if len(searchResList)>0:
            appId=searchResList[0]
        logging.debug('getAppId: appId is '+appId)
        return appId       

    def getIosLoaderType(self,appId):
        logging.debug('getIosLoaderType: begin getIosLoaderType')
        appIdPath=os.path.join(self.__curDir,'appLoader','custom-loader-ios',appId)
        logging.debug('getIosLoaderType: appIdPath is '+os.path.join(appIdPath,'load.conf'))
        
        if os.path.exists(os.path.join(appIdPath,'load.conf')) and os.path.exists(os.path.join(appIdPath,'load.ipa')):
            logging.debug('getIosLoaderType: It is may a customerized loader.')
            with open(os.path.join(appIdPath,'load.conf')) as f:
                config=json.load(f)
                logging.debug('getIosLoaderType: load.conf content is '+str(config))
                if 'version' in config:
                    version=config['version'].strip()
                if 'packageName' in config:
                    pkgName=config['packageName'].strip()
                if 'ignore' in config:
                    self.__ignore==config['ignore']

                if len(version)>0 and len(pkgName)>0:
                    self.__pkgName=pkgName
                    self.__loaderName='custom-loader-ios'+os.path.sep+appId
                logging.debug('getIosLoaderType: pkgName is '+self.__pkgName)
        else:
            self.__pkgName='com.apicloud.apploader'
            self.__loaderName='apicloud-loader-ios'    
            logging.debug('getIosLoaderType: path not exiest, will use default appLoader') 
        pass         

class EnApicloudLoaderIosCommand(sublime_plugin.WindowCommand):
    """docstring for ApicloudIOSLoaderCommand"""
    __adbExe='' 
    __curDir=''
    __pkgName='com.apicloud.apploader'
    __loaderName='apicloud-loader'
    __cmdLogType='' #logFile
    __ignore=['.svn','.git']

    def __init__(self,arg):
        self.__curDir=curDir
    
    def is_visible(self, dirs): 
        return len(dirs) > 0 and settings.get("envlang") == "en"

    def is_enabled(self, dirs):
        if 0==len(dirs):
            return False
        appFileList=os.listdir(dirs[0])
        if 'config.xml' in appFileList:
            return True
        return False

    def run(self, dirs):
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(message)s',
            datefmt='%Y %m %d  %H:%M:%S',
            filename=os.path.join(self.__curDir,'apicloud.log'),
            filemode='a')
        sublime.status_message(u'IOS Sync started')
        logging.debug('*'*30+'begin ios sync'+'*'*30)
        logging.debug('sync dir is '+dirs[0])
        try:
            BeforeSystemRequests()
            self.loadIos(dirs[0])
        except:
            logging.debug('run: exception happened as below')
            errMsg=traceback.format_exc()
            logging.debug(errMsg)
            print(errMsg)
            sublime.error_message(u'IOS Sync abnormal')

        sublime.status_message(u'IOS Sync completed')
        logging.debug('*'*30+'ios sync complete'+'*'*30)

    def CleanDir(self, Dir):
        if os.path.isdir( Dir ):
            paths = os.listdir( Dir )
            for path in paths:
                filePath = os.path.join( Dir, path )
                if os.path.isfile( filePath ):
                    try:
                        os.remove( filePath )
                    except os.error:
                        autoRun.exception( "remove %s error." %filePath )
                elif os.path.isdir( filePath ):
                    shutil.rmtree(filePath,True)
        return True        

    def loadIos(self, srcPath):
        logging.debug('loadIos: current dir is ')
        if 'windows' in platform.system().lower():
            if not os.path.exists(os.path.join(self.__curDir,'tools','jre','bin')) :
                logging.debug('loadIos: cannot find load.conf')
                sublime.error_message(u'缺少JRE环境')
                return
        else: 
            (rtnCode,stdout,stderr)=runShellCommand('java -version',self.__cmdLogType)
            outputMsg=stdout+stderr
            if 'version' not in outputMsg:
                sublime.error_message(u'JRE environment is missing')
                return
        if not os.path.exists(os.path.join(self.__curDir,'appLoader','apicloud-loader-ios','load.conf')) or not os.path.exists(os.path.join(self.__curDir,'appLoader','apicloud-loader','load.apk')):
            logging.debug('loadIos: cannot find load.conf')
            sublime.error_message(u'Some files are missing: "load.conf"')
            return
        appId=self.getAppId(srcPath)
        self.getIosLoaderType(appId)
        logging.debug('loadIos: appId is '+ str(appId))
        if -1==appId:
            sublime.error_message(u'Please make sure the directory is correct')
            return

        if 'windows' in platform.system().lower():
            javaCmd=os.path.join(self.__curDir,'tools','jre','bin','java')
        else:
            javaCmd='java'

        fulldirname=os.path.abspath(srcPath)  
        tmpPathName='tmp-apicloud-folder'
        tmpPath=os.path.join(os.path.dirname(srcPath),tmpPathName)
        # force delete .git which is read only
        for (p,d,f) in os.walk(tmpPath):  
            if p.find('.git')>0:  
                if 'windows' in platform.system().lower():
                    os.popen('rd /s /q %s'%p) 
                elif 'darwin' in platform.system().lower():
                    os.popen('rm -rf %s'%p)
                elif 'linux' in platform.system().lower():
                    os.popen('rm -rf %s'%p)     
        if os.path.exists(tmpPath):
            self.CleanDir(tmpPath)
            os.rmdir(tmpPath)
        shutil.copytree(srcPath,tmpPath,ignore = shutil.ignore_patterns(*self.__ignore))

        jarFile=os.path.join(self.__curDir,'tools','syncapp.jar')
        iosLoaderPath=os.path.join(self.__curDir,'appLoader',self.__loaderName)
        versionFile=os.path.join(iosLoaderPath,'load.conf')
        iosLoaderFile=os.path.join(iosLoaderPath,'load.ipa')

        iosSyncCmd='"'+javaCmd+'" -jar "'+jarFile+'" "'+srcPath+'" "'+iosLoaderPath+'" "'+iosLoaderFile+'" "'+versionFile+'"'
        logging.debug('loadIos: cmd is'+iosSyncCmd)
        (rtnCode,stdout,stderr)=runShellCommand(iosSyncCmd,self.__cmdLogType)
        outputMsg=stdout+stderr
        logging.debug('loadIos: outputMsg is '+outputMsg)
        self.CleanDir(tmpPath)
        os.rmdir(tmpPath)
        
        if 'No iOS device attached' in outputMsg:
            sublime.error_message(u'no ios device found !')
            logging.debug('loadIos: no ios device found !')
        elif 'error' in outputMsg or 'failed' in outputMsg:
            logging.debug('loadIos: failed to sync ios')
            sublime.error_message(u'IOS Sync failed')
        else:
            logging.debug('loadIos: ios sync success.')
            sublime.message_dialog(u'IOS sync success')

    def getAppId(self, srcPath):
        logging.debug('begin getAppId: srcPath is '+srcPath)
        appId=-1
        if not os.path.exists(srcPath) or not os.path.isdir(srcPath):
            logging.debug('getAppId:file no exist or not a folder!')
            return appId
        appFileList=os.listdir(srcPath)
        if 'config.xml' not in appFileList:
            logging.debug('getAppId: please make sure sync the correct folder!')
            return -1
        with open(os.path.join(srcPath,"config.xml"),encoding='utf-8') as f:
            fileContent=f.read()
            r=re.compile(r"widget.*id.*=.*(A[0-9]{13})\"")
            searchResList=r.findall(fileContent)  
        if len(searchResList)>0:
            appId=searchResList[0]
        logging.debug('getAppId: appId is '+appId)
        return appId       

    def getIosLoaderType(self,appId):
        logging.debug('getIosLoaderType: begin getIosLoaderType')
        appIdPath=os.path.join(self.__curDir,'appLoader','custom-loader-ios',appId)
        logging.debug('getIosLoaderType: appIdPath is '+os.path.join(appIdPath,'load.conf'))
        
        if os.path.exists(os.path.join(appIdPath,'load.conf')) and os.path.exists(os.path.join(appIdPath,'load.ipa')):
            logging.debug('getIosLoaderType: It is may a customerized loader.')
            with open(os.path.join(appIdPath,'load.conf')) as f:
                config=json.load(f)
                logging.debug('getIosLoaderType: load.conf content is '+str(config))
                if 'version' in config:
                    version=config['version'].strip()
                if 'packageName' in config:
                    pkgName=config['packageName'].strip()
                if 'ignore' in config:
                    self.__ignore==config['ignore']

                if len(version)>0 and len(pkgName)>0:
                    self.__pkgName=pkgName
                    self.__loaderName='custom-loader-ios'+os.path.sep+appId
                logging.debug('getIosLoaderType: pkgName is '+self.__pkgName)
        else:
            self.__pkgName='com.apicloud.apploader'
            self.__loaderName='apicloud-loader-ios'    
            logging.debug('getIosLoaderType: path not exiest, will use default appLoader') 
        pass         

class FrApicloudLoaderIosCommand(sublime_plugin.WindowCommand):
    """docstring for ApicloudIOSLoaderCommand"""
    __adbExe='' 
    __curDir=''
    __pkgName='com.apicloud.apploader'
    __loaderName='apicloud-loader'
    __cmdLogType='' #logFile
    __ignore=['.svn','.git']

    def __init__(self,arg):
        self.__curDir=curDir
    
    def is_visible(self, dirs): 
        return len(dirs) > 0 and settings.get("envlang") == "fr"

    def is_enabled(self, dirs):
        if 0==len(dirs):
            return False
        appFileList=os.listdir(dirs[0])
        if 'config.xml' in appFileList:
            return True
        return False

    def run(self, dirs):
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(message)s',
            datefmt='%Y %m %d  %H:%M:%S',
            filename=os.path.join(self.__curDir,'apicloud.log'),
            filemode='a')
        sublime.status_message(u'Demarrage de la synchronisation IOS')
        logging.debug('*'*30+'begin ios sync'+'*'*30)
        logging.debug('sync dir is '+dirs[0])
        try:
            BeforeSystemRequests()
            self.loadIos(dirs[0])
        except:
            logging.debug('run: exception happened as below')
            errMsg=traceback.format_exc()
            logging.debug(errMsg)
            print(errMsg)
            sublime.error_message(u'Synchronisation IOS anormal')

        sublime.status_message(u'Synchronisation achevE avec succes')
        logging.debug('*'*30+'ios sync complete'+'*'*30)

    def CleanDir(self, Dir):
        if os.path.isdir( Dir ):
            paths = os.listdir( Dir )
            for path in paths:
                filePath = os.path.join( Dir, path )
                if os.path.isfile( filePath ):
                    try:
                        os.remove( filePath )
                    except os.error:
                        autoRun.exception( "remove %s error." %filePath )
                elif os.path.isdir( filePath ):
                    shutil.rmtree(filePath,True)
        return True        

    def loadIos(self, srcPath):
        logging.debug('loadIos: current dir is ')
        if 'windows' in platform.system().lower():
            if not os.path.exists(os.path.join(self.__curDir,'tools','jre','bin')) :
                logging.debug('loadIos: cannot find load.conf')
                sublime.error_message(u'缺少JRE环境')
                return
        else: 
            (rtnCode,stdout,stderr)=runShellCommand('java -version',self.__cmdLogType)
            outputMsg=stdout+stderr
            if 'version' not in outputMsg:
                sublime.error_message(u'Environnement JRE inexistant')
                return
        if not os.path.exists(os.path.join(self.__curDir,'appLoader','apicloud-loader-ios','load.conf')) or not os.path.exists(os.path.join(self.__curDir,'appLoader','apicloud-loader','load.apk')):
            logging.debug('loadIos: cannot find load.conf')
            sublime.error_message(u'Fichier introuvable: "load.conf"')
            return
        appId=self.getAppId(srcPath)
        self.getIosLoaderType(appId)
        logging.debug('loadIos: appId is '+ str(appId))
        if -1==appId:
            sublime.error_message(u'Assurez vous que le repertoire est le bon')
            return

        if 'windows' in platform.system().lower():
            javaCmd=os.path.join(self.__curDir,'tools','jre','bin','java')
        else:
            javaCmd='java'

        fulldirname=os.path.abspath(srcPath)  
        tmpPathName='tmp-apicloud-folder'
        tmpPath=os.path.join(os.path.dirname(srcPath),tmpPathName)
        # force delete .git which is read only
        for (p,d,f) in os.walk(tmpPath):  
            if p.find('.git')>0:  
                if 'windows' in platform.system().lower():
                    os.popen('rd /s /q %s'%p) 
                elif 'darwin' in platform.system().lower():
                    os.popen('rm -rf %s'%p)
                elif 'linux' in platform.system().lower():
                    os.popen('rm -rf %s'%p)     
        if os.path.exists(tmpPath):
            self.CleanDir(tmpPath)
            os.rmdir(tmpPath)
        shutil.copytree(srcPath,tmpPath,ignore = shutil.ignore_patterns(*self.__ignore))

        jarFile=os.path.join(self.__curDir,'tools','syncapp.jar')
        iosLoaderPath=os.path.join(self.__curDir,'appLoader',self.__loaderName)
        versionFile=os.path.join(iosLoaderPath,'load.conf')
        iosLoaderFile=os.path.join(iosLoaderPath,'load.ipa')

        iosSyncCmd='"'+javaCmd+'" -jar "'+jarFile+'" "'+srcPath+'" "'+iosLoaderPath+'" "'+iosLoaderFile+'" "'+versionFile+'"'
        logging.debug('loadIos: cmd is'+iosSyncCmd)
        (rtnCode,stdout,stderr)=runShellCommand(iosSyncCmd,self.__cmdLogType)
        outputMsg=stdout+stderr
        logging.debug('loadIos: outputMsg is '+outputMsg)
        self.CleanDir(tmpPath)
        os.rmdir(tmpPath)
        
        if 'No iOS device attached' in outputMsg:
            sublime.error_message(u'Aucun terminal IOS n''a ete trouve, verifiez la connexion')
            logging.debug('loadIos: no ios device found !')
        elif 'error' in outputMsg or 'failed' in outputMsg:
            logging.debug('loadIos: failed to sync ios')
            sublime.error_message(u'Echec de la synchronisation IOS')
        else:
            logging.debug('loadIos: ios sync success.')
            sublime.message_dialog(u'Synchronisation IOS finie avec succes')

    def getAppId(self, srcPath):
        logging.debug('begin getAppId: srcPath is '+srcPath)
        appId=-1
        if not os.path.exists(srcPath) or not os.path.isdir(srcPath):
            logging.debug('getAppId:file no exist or not a folder!')
            return appId
        appFileList=os.listdir(srcPath)
        if 'config.xml' not in appFileList:
            logging.debug('getAppId: please make sure sync the correct folder!')
            return -1
        with open(os.path.join(srcPath,"config.xml"),encoding='utf-8') as f:
            fileContent=f.read()
            r=re.compile(r"widget.*id.*=.*(A[0-9]{13})\"")
            searchResList=r.findall(fileContent)  
        if len(searchResList)>0:
            appId=searchResList[0]
        logging.debug('getAppId: appId is '+appId)
        return appId       

    def getIosLoaderType(self,appId):
        logging.debug('getIosLoaderType: begin getIosLoaderType')
        appIdPath=os.path.join(self.__curDir,'appLoader','custom-loader-ios',appId)
        logging.debug('getIosLoaderType: appIdPath is '+os.path.join(appIdPath,'load.conf'))
        
        if os.path.exists(os.path.join(appIdPath,'load.conf')) and os.path.exists(os.path.join(appIdPath,'load.ipa')):
            logging.debug('getIosLoaderType: It is may a customerized loader.')
            with open(os.path.join(appIdPath,'load.conf')) as f:
                config=json.load(f)
                logging.debug('getIosLoaderType: load.conf content is '+str(config))
                if 'version' in config:
                    version=config['version'].strip()
                if 'packageName' in config:
                    pkgName=config['packageName'].strip()
                if 'ignore' in config:
                    self.__ignore==config['ignore']

                if len(version)>0 and len(pkgName)>0:
                    self.__pkgName=pkgName
                    self.__loaderName='custom-loader-ios'+os.path.sep+appId
                logging.debug('getIosLoaderType: pkgName is '+self.__pkgName)
        else:
            self.__pkgName='com.apicloud.apploader'
            self.__loaderName='apicloud-loader-ios'    
            logging.debug('getIosLoaderType: path not exiest, will use default appLoader') 
        pass         

import os,platform,uuid,urllib.parse,urllib.request,json
def BeforeSystemRequests():
    '''
    the systeminfo uploads to api of ..
    '''
    def get_system_version():
        system_name = platform.system()
        if system_name == 'Windows' and os.name == 'nt':
            system_machine = platform.platform().split('-')[0] + platform.platform().split('-')[1]
        elif system_name == 'Darwin':
            system_machine = 'Mac-os'
        else:
            system_machine = system_name
        return system_machine

    def post(url,data):
        data = urllib.parse.urlencode({'info':data}).encode('utf-8')
        req = urllib.request.Request(url,data)
        urllib.request.urlopen(req)
        return
    def index():
        apiUrl = 'http://www.apicloud.com/setSublimeInfo'
        systemInfo = {
            "system": get_system_version(),
            "uuid": hex(uuid.getnode())
        }
        try:
            systemInfo = json.dumps(systemInfo) 
            post(apiUrl,systemInfo)
        except Exception as e:
            print('exception is :',e)
        finally:
            pass
    try:        
        index()
    except Exception as e:
        pass   

import functools
class NewApicloudDefaultAppCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        self.window.show_input_panel("新建 APICloud 项目名称:", "", functools.partial(self.on_done, dirs[0]), None, None)

    def on_done(self, dir, name):
        import shutil
        shutil.copytree(os.path.join(curDir,'appLoader','widget','default'),os.path.join(dir, name))
        if 'windows' in platform.system().lower():
            desFile=os.path.join(dir, name)+"\\config.xml"
        elif 'darwin' in platform.system().lower():
            desFile=os.path.join(dir, name)+"/config.xml"
        elif 'linux' in platform.system().lower():
            desFile=os.path.join(dir, name)+"/config.xml"
        inputFile=open(desFile,encoding='utf-8')  
        lines=inputFile.readlines()  
        inputFile.close()
        outputFile =open(desFile,'w',encoding='utf-8'); 
        for line in lines:
            if '<name>' in line: 
                line='    <name>'+name+'</name>\n'
                outputFile.write(line) 
            else:    
                outputFile.write(line) 
        outputFile.close()      

    def is_visible(self, dirs):
        return len(dirs) == 1 and not (settings.get("envlang") == "en" or settings.get("envlang") == "fr")

class EnNewApicloudDefaultAppCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        self.window.show_input_panel("New APICloud project's name:", "", functools.partial(self.on_done, dirs[0]), None, None)

    def on_done(self, dir, name):
        import shutil
        shutil.copytree(os.path.join(curDir,'appLoader','widget','default'),os.path.join(dir, name))
        if 'windows' in platform.system().lower():
            desFile=os.path.join(dir, name)+"\\config.xml"
        elif 'darwin' in platform.system().lower():
            desFile=os.path.join(dir, name)+"/config.xml"
        elif 'linux' in platform.system().lower():
            desFile=os.path.join(dir, name)+"/config.xml"
        inputFile=open(desFile,encoding='utf-8')  
        lines=inputFile.readlines()  
        inputFile.close()
        outputFile =open(desFile,'w',encoding='utf-8'); 
        for line in lines:
            if '<name>' in line: 
                line='    <name>'+name+'</name>\n'
                outputFile.write(line) 
            else:    
                outputFile.write(line) 
        outputFile.close()      

    def is_visible(self, dirs):
        return len(dirs) == 1 and settings.get("envlang") == "en"

class FrNewApicloudDefaultAppCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        self.window.show_input_panel("Nom du nouveau projet APICloud:", "", functools.partial(self.on_done, dirs[0]), None, None)

    def on_done(self, dir, name):
        import shutil
        shutil.copytree(os.path.join(curDir,'appLoader','widget','default'),os.path.join(dir, name))
        if 'windows' in platform.system().lower():
            desFile=os.path.join(dir, name)+"\\config.xml"
        elif 'darwin' in platform.system().lower():
            desFile=os.path.join(dir, name)+"/config.xml"
        elif 'linux' in platform.system().lower():
            desFile=os.path.join(dir, name)+"/config.xml"
        inputFile=open(desFile,encoding='utf-8')  
        lines=inputFile.readlines()  
        inputFile.close()
        outputFile =open(desFile,'w',encoding='utf-8'); 
        for line in lines:
            if '<name>' in line: 
                line='    <name>'+name+'</name>\n'
                outputFile.write(line) 
            else:    
                outputFile.write(line) 
        outputFile.close()      

    def is_visible(self, dirs):
        return len(dirs) == 1 and settings.get("envlang") == "fr"      

class NewApicloudBottomAppCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        self.window.show_input_panel("新建 APICloud 项目名称:", "", functools.partial(self.on_done, dirs[0]), None, None)

    def on_done(self, dir, name):
        import shutil
        shutil.copytree(os.path.join(curDir,'appLoader','widget','bottom'),os.path.join(dir, name))
        if 'windows' in platform.system().lower():
            desFile=os.path.join(dir, name)+"\\config.xml"
        elif 'darwin' in platform.system().lower():
            desFile=os.path.join(dir, name)+"/config.xml"
        elif 'linux' in platform.system().lower():
            desFile=os.path.join(dir, name)+"/config.xml"
        inputFile=open(desFile,encoding='utf-8')  
        lines=inputFile.readlines()  
        inputFile.close()
        outputFile =open(desFile,'w',encoding='utf-8'); 
        for line in lines:
            if '<name>' in line: 
                line='  <name>'+name+'</name>\n'
                outputFile.write(line) 
            else:    
                outputFile.write(line) 
        outputFile.close()      

    def is_visible(self, dirs):
        return len(dirs) == 1 and not (settings.get("envlang") == "en" or settings.get("envlang") == "fr")

class EnNewApicloudBottomAppCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        self.window.show_input_panel("New APICloud project's name:", "", functools.partial(self.on_done, dirs[0]), None, None)

    def on_done(self, dir, name):
        import shutil
        shutil.copytree(os.path.join(curDir,'appLoader','widget','bottom'),os.path.join(dir, name))
        if 'windows' in platform.system().lower():
            desFile=os.path.join(dir, name)+"\\config.xml"
        elif 'darwin' in platform.system().lower():
            desFile=os.path.join(dir, name)+"/config.xml"
        elif 'linux' in platform.system().lower():
            desFile=os.path.join(dir, name)+"/config.xml"
        inputFile=open(desFile,encoding='utf-8')  
        lines=inputFile.readlines()  
        inputFile.close()
        outputFile =open(desFile,'w',encoding='utf-8'); 
        for line in lines:
            if '<name>' in line: 
                line='  <name>'+name+'</name>\n'
                outputFile.write(line) 
            else:    
                outputFile.write(line) 
        outputFile.close()      

    def is_visible(self, dirs):
        return len(dirs) == 1 and settings.get("envlang") == "en"

class FrNewApicloudBottomAppCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        self.window.show_input_panel("Nom du nouveau projet APICloud:", "", functools.partial(self.on_done, dirs[0]), None, None)

    def on_done(self, dir, name):
        import shutil
        shutil.copytree(os.path.join(curDir,'appLoader','widget','bottom'),os.path.join(dir, name))
        if 'windows' in platform.system().lower():
            desFile=os.path.join(dir, name)+"\\config.xml"
        elif 'darwin' in platform.system().lower():
            desFile=os.path.join(dir, name)+"/config.xml"
        elif 'linux' in platform.system().lower():
            desFile=os.path.join(dir, name)+"/config.xml"
        inputFile=open(desFile,encoding='utf-8')  
        lines=inputFile.readlines()  
        inputFile.close()
        outputFile =open(desFile,'w',encoding='utf-8'); 
        for line in lines:
            if '<name>' in line: 
                line='  <name>'+name+'</name>\n'
                outputFile.write(line) 
            else:    
                outputFile.write(line) 
        outputFile.close()      

    def is_visible(self, dirs):
        return len(dirs) == 1 and settings.get("envlang") == "fr"

class NewApicloudHomeAppCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        self.window.show_input_panel("新建 APICloud 项目名称:", "", functools.partial(self.on_done, dirs[0]), None, None)

    def on_done(self, dir, name):
        import shutil
        shutil.copytree(os.path.join(curDir,'appLoader','widget','home'),os.path.join(dir, name))
        if 'windows' in platform.system().lower():
            desFile=os.path.join(dir, name)+"\\config.xml"
        elif 'darwin' in platform.system().lower():
            desFile=os.path.join(dir, name)+"/config.xml"
        elif 'linux' in platform.system().lower():
            desFile=os.path.join(dir, name)+"/config.xml"
        inputFile=open(desFile,encoding='utf-8')  
        lines=inputFile.readlines()  
        inputFile.close()
        outputFile =open(desFile,'w',encoding='utf-8'); 
        for line in lines:
            if '<name>' in line: 
                line='  <name>'+name+'</name>\n'
                outputFile.write(line) 
            else:    
                outputFile.write(line) 
        outputFile.close()      

    def is_visible(self, dirs):
        return len(dirs) == 1 and not (settings.get("envlang") == "en" or settings.get("envlang") == "fr")

class EnNewApicloudHomeAppCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        self.window.show_input_panel("New APICloud projec's name:", "", functools.partial(self.on_done, dirs[0]), None, None)

    def on_done(self, dir, name):
        import shutil
        shutil.copytree(os.path.join(curDir,'appLoader','widget','home'),os.path.join(dir, name))
        if 'windows' in platform.system().lower():
            desFile=os.path.join(dir, name)+"\\config.xml"
        elif 'darwin' in platform.system().lower():
            desFile=os.path.join(dir, name)+"/config.xml"
        elif 'linux' in platform.system().lower():
            desFile=os.path.join(dir, name)+"/config.xml"
        inputFile=open(desFile,encoding='utf-8')  
        lines=inputFile.readlines()  
        inputFile.close()
        outputFile =open(desFile,'w',encoding='utf-8'); 
        for line in lines:
            if '<name>' in line: 
                line='  <name>'+name+'</name>\n'
                outputFile.write(line) 
            else:    
                outputFile.write(line) 
        outputFile.close()      

    def is_visible(self, dirs):
        return len(dirs) == 1 and settings.get("envlang") == "en"              

class FrNewApicloudHomeAppCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        self.window.show_input_panel("Nom du nouveau projet APICloud:", "", functools.partial(self.on_done, dirs[0]), None, None)

    def on_done(self, dir, name):
        import shutil
        shutil.copytree(os.path.join(curDir,'appLoader','widget','home'),os.path.join(dir, name))
        if 'windows' in platform.system().lower():
            desFile=os.path.join(dir, name)+"\\config.xml"
        elif 'darwin' in platform.system().lower():
            desFile=os.path.join(dir, name)+"/config.xml"
        elif 'linux' in platform.system().lower():
            desFile=os.path.join(dir, name)+"/config.xml"
        inputFile=open(desFile,encoding='utf-8')  
        lines=inputFile.readlines()  
        inputFile.close()
        outputFile =open(desFile,'w',encoding='utf-8'); 
        for line in lines:
            if '<name>' in line: 
                line='  <name>'+name+'</name>\n'
                outputFile.write(line) 
            else:    
                outputFile.write(line) 
        outputFile.close()      

    def is_visible(self, dirs):
        return len(dirs) == 1 and settings.get("envlang") == "fr"               

class NewApicloudSlideAppCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        self.window.show_input_panel("新建 APICloud 项目名称:", "", functools.partial(self.on_done, dirs[0]), None, None)

    def on_done(self, dir, name):
        import shutil
        shutil.copytree(os.path.join(curDir,'appLoader','widget','slide'),os.path.join(dir, name))
        if 'windows' in platform.system().lower():
            desFile=os.path.join(dir, name)+"\\config.xml"
        elif 'darwin' in platform.system().lower():
            desFile=os.path.join(dir, name)+"/config.xml"
        elif 'linux' in platform.system().lower():
            desFile=os.path.join(dir, name)+"/config.xml"
        inputFile=open(desFile,encoding='utf-8')  
        lines=inputFile.readlines()  
        inputFile.close()
        outputFile =open(desFile,'w',encoding='utf-8'); 
        for line in lines:
            if '<name>' in line: 
                line='  <name>'+name+'</name>\n'
                outputFile.write(line) 
            else:    
                outputFile.write(line) 
        outputFile.close()      

    def is_visible(self, dirs):
        return len(dirs) == 1 and not (settings.get("envlang") == "en" or settings.get("envlang") == "fr")

class EnNewApicloudSlideAppCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        self.window.show_input_panel("New APICloud projec's name:", "", functools.partial(self.on_done, dirs[0]), None, None)

    def on_done(self, dir, name):
        import shutil
        shutil.copytree(os.path.join(curDir,'appLoader','widget','slide'),os.path.join(dir, name))
        if 'windows' in platform.system().lower():
            desFile=os.path.join(dir, name)+"\\config.xml"
        elif 'darwin' in platform.system().lower():
            desFile=os.path.join(dir, name)+"/config.xml"
        elif 'linux' in platform.system().lower():
            desFile=os.path.join(dir, name)+"/config.xml"
        inputFile=open(desFile,encoding='utf-8')  
        lines=inputFile.readlines()  
        inputFile.close()
        outputFile =open(desFile,'w',encoding='utf-8'); 
        for line in lines:
            if '<name>' in line: 
                line='  <name>'+name+'</name>\n'
                outputFile.write(line) 
            else:    
                outputFile.write(line) 
        outputFile.close()      

    def is_visible(self, dirs):
        return len(dirs) == 1 and settings.get("envlang") == "en"

class FrNewApicloudSlideAppCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        self.window.show_input_panel("Nom du nouveau projet APICloud:", "", functools.partial(self.on_done, dirs[0]), None, None)

    def on_done(self, dir, name):
        import shutil
        shutil.copytree(os.path.join(curDir,'appLoader','widget','slide'),os.path.join(dir, name))
        if 'windows' in platform.system().lower():
            desFile=os.path.join(dir, name)+"\\config.xml"
        elif 'darwin' in platform.system().lower():
            desFile=os.path.join(dir, name)+"/config.xml"
        elif 'linux' in platform.system().lower():
            desFile=os.path.join(dir, name)+"/config.xml"
        inputFile=open(desFile,encoding='utf-8')  
        lines=inputFile.readlines()  
        inputFile.close()
        outputFile =open(desFile,'w',encoding='utf-8'); 
        for line in lines:
            if '<name>' in line: 
                line='  <name>'+name+'</name>\n'
                outputFile.write(line) 
            else:    
                outputFile.write(line) 
        outputFile.close()      

    def is_visible(self, dirs):
        return len(dirs) == 1 and settings.get("envlang") == "fr"


import zipfile
class CompressWidgetCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(message)s',
            datefmt='%Y %m %d  %H:%M:%S',
            filename=os.path.join(curDir,'apicloud.log'),
            filemode='a')
        dirname=dirs[0]
        filelist=[]  
        fulldirname=os.path.abspath(dirname)  
        zipfilename=os.path.basename(fulldirname)+'.zip'
        fullzipfilename=os.path.join(os.path.dirname(fulldirname),zipfilename)  
        logging.debug('*'*30+'begin CompressWidgetCommand'+'*'*30)
        logging.debug("CompressWidgetCommand: Begin to zip %s to %s ..." % (fulldirname, fullzipfilename)  )
        if not os.path.exists(fulldirname):  
            logging.debug( "CompressWidgetCommand: Folder %s is not exist" % fulldirname  )
            sublime.error_message(u"文件夹 %s 不存在!" % fulldirname)
            return  
        if os.path.exists(fullzipfilename):      
            flag=sublime.ok_cancel_dialog(u"文件%s 已存在，确定覆盖该文件 ? [Y/N]" % fullzipfilename)
            logging.debug("CompressWidgetCommand: %s has already exist" % fullzipfilename  )
            if not flag:
                logging.debug('CompressWidgetCommand: cancel zip the folder')
                return

        for root, dirlist, files in os.walk(dirname):  
            for filename in files:  
                filelist.append(os.path.join(root,filename))  

        destZip=zipfile.ZipFile(fullzipfilename, "w")  
        for eachfile in filelist:  
            destfile=eachfile[len(dirname):]  
            sublime.status_message(u"正在压缩文件 file %s." % destfile )
            logging.debug("CompressWidgetCommand: Zip file %s." % destfile  )
            destZip.write(eachfile, 'widget'+destfile)  
        destZip.close()  
        sublime.status_message(u'压缩完成')
        logging.debug("CompressWidgetCommand: Zip folder succeed!")        
        logging.debug('*'*30+'CompressWidgetCommand complete'+'*'*30)

    def is_visible(self, dirs):
        return len(dirs) == 1 and not (settings.get("envlang") == "en" or settings.get("envlang") == "fr")     

    def is_enabled(self, dirs):
        if 0==len(dirs):
            return False
        appFileList=os.listdir(dirs[0])
        if 'config.xml' in appFileList:
            return True
        return False

class EnCompressWidgetCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(message)s',
            datefmt='%Y %m %d  %H:%M:%S',
            filename=os.path.join(curDir,'apicloud.log'),
            filemode='a')
        dirname=dirs[0]
        filelist=[]  
        fulldirname=os.path.abspath(dirname)  
        zipfilename=os.path.basename(fulldirname)+'.zip'
        fullzipfilename=os.path.join(os.path.dirname(fulldirname),zipfilename)  
        logging.debug('*'*30+'begin CompressWidgetCommand'+'*'*30)
        logging.debug("CompressWidgetCommand: Begin to zip %s to %s ..." % (fulldirname, fullzipfilename)  )
        if not os.path.exists(fulldirname):  
            logging.debug( "CompressWidgetCommand: Folder %s is not exist" % fulldirname  )
            sublime.error_message(u"Folder %s does not exist!" % fulldirname)
            return  
        if os.path.exists(fullzipfilename):      
            flag=sublime.ok_cancel_dialog(u"File %s already exists，do want override it ? [Y/N]" % fullzipfilename)
            logging.debug("CompressWidgetCommand: %s has already exist" % fullzipfilename  )
            if not flag:
                logging.debug('CompressWidgetCommand: cancel zip the folder')
                return

        for root, dirlist, files in os.walk(dirname):  
            for filename in files:  
                filelist.append(os.path.join(root,filename))  

        destZip=zipfile.ZipFile(fullzipfilename, "w")  
        for eachfile in filelist:  
            destfile=eachfile[len(dirname):]  
            sublime.status_message(u"Zipping file %s." % destfile )
            logging.debug("CompressWidgetCommand: Zip file %s." % destfile  )
            destZip.write(eachfile, 'widget'+destfile)  
        destZip.close()  
        sublime.status_message(u'Compression done !')
        logging.debug("CompressWidgetCommand: Zip folder succeed!")        
        logging.debug('*'*30+'CompressWidgetCommand complete'+'*'*30)

    def is_visible(self, dirs):
        return len(dirs) == 1 and settings.get("envlang") == "en"     

    def is_enabled(self, dirs):
        if 0==len(dirs):
            return False
        appFileList=os.listdir(dirs[0])
        if 'config.xml' in appFileList:
            return True
        return False

class FrCompressWidgetCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(message)s',
            datefmt='%Y %m %d  %H:%M:%S',
            filename=os.path.join(curDir,'apicloud.log'),
            filemode='a')
        dirname=dirs[0]
        filelist=[]  
        fulldirname=os.path.abspath(dirname)  
        zipfilename=os.path.basename(fulldirname)+'.zip'
        fullzipfilename=os.path.join(os.path.dirname(fulldirname),zipfilename)  
        logging.debug('*'*30+'begin CompressWidgetCommand'+'*'*30)
        logging.debug("CompressWidgetCommand: Begin to zip %s to %s ..." % (fulldirname, fullzipfilename)  )
        if not os.path.exists(fulldirname):  
            logging.debug( "CompressWidgetCommand: Folder %s does not exist" % fulldirname  )
            sublime.error_message(u"Repertoire %s inexistant!" % fulldirname)
            return  
        if os.path.exists(fullzipfilename):      
            flag=sublime.ok_cancel_dialog(u"Le fichier %s existe deja，souhaitez vous l'ecraser ? [Y/N]" % fullzipfilename)
            logging.debug("CompressWidgetCommand: %s already exists" % fullzipfilename  )
            if not flag:
                logging.debug('CompressWidgetCommand: cancel zip the folder')
                return

        for root, dirlist, files in os.walk(dirname):  
            for filename in files:  
                filelist.append(os.path.join(root,filename))  

        destZip=zipfile.ZipFile(fullzipfilename, "w")  
        for eachfile in filelist:  
            destfile=eachfile[len(dirname):]  
            sublime.status_message(u"Compression du fichier %s." % destfile )
            logging.debug("CompressWidgetCommand: Zip file %s." % destfile  )
            destZip.write(eachfile, 'widget'+destfile)  
        destZip.close()  
        sublime.status_message(u'Compression terminee avec succes')
        logging.debug("CompressWidgetCommand: Zip folder succeed!")        
        logging.debug('*'*30+'CompressWidgetCommand complete'+'*'*30)

    def is_visible(self, dirs):
        return len(dirs) == 1 and settings.get("envlang") == "fr"      

    def is_enabled(self, dirs):
        if 0==len(dirs):
            return False
        appFileList=os.listdir(dirs[0])
        if 'config.xml' in appFileList:
            return True
        return False
