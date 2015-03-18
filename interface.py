#!/usr/bin/python
# -*- coding:utf-8 -*-
#---------------------------------------------------------------------------
# FileName:     Interface.py
# Description:  取自wxpython demo(通过对其修改完成)   
# Author:       Xiongkunpeng
# Version:      0.0.1
# Created:      2011-09-06
# Company:      CASCO
# LastChange:   create 2011-09-07
# History:          
#----------------------------------------------------------------------------
import wx
#import wx.grid
#from interface import simplecontrol
from interface import cuscontrol
from interface import simpleplot
from interface import simplepanel
from interface import simplewizard
from interface import devicecfgframe
from interface import devicemsgcfgframe
import os
import sys        
from simmain import TPSim
from base import commlib
from base.caseprocess import CaseParser
import  wx.lib.filebrowsebutton as filebrowse
# import matplotlib.pyplot as Mplt   #用于画图
import time 
import Queue
from base.mthread import MThread
import threading
import gc
from base.omapparser import OMAPParser
from base.omapparser import OMAPFigureConfigHandle
from base import excepthandle
from base.loglog import LogLog
from autoAnalysis.resultanalysis import ResultAnalysis
from GradientButton import MyGradientButton
from GradientButton import TrainSimulator
from Car import Car
#import wx.lib.platebtn as platebtn

#from wx.lib.embeddedimage import PyEmbeddedImage

try:
    dirName = os.path.dirname( os.path.abspath( __file__ ) )
except:
    dirName = os.path.dirname( os.path.abspath( sys.argv[0] ) )

sys.path.append( os.path.split( dirName )[0] )

try:
    from agw import aui
    from agw.aui import aui_switcherdialog as ASD
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.aui as aui
    from wx.lib.agw.aui import aui_switcherdialog as ASD

import random
from interface import images


class AuiFrame( wx.Frame ):
    "test platform main interface."
    
    RunQ = None  #AuiFram 本队列用于存储需要顺序执行的，每个包为一个元组（函数，参数列表）
    #控制刷新testcaseconfigpanel的变量
    old_config_panel_size = None
    new_config_panel_size = None
    
    def __init__( self, parent, id = wx.ID_ANY, title = "", pos = wx.DefaultPosition,
                 size = wx.DefaultSize, style = wx.DEFAULT_FRAME_STYLE | wx.SUNKEN_BORDER ):

        wx.Frame.__init__( self, parent, id, title, pos, size, style )
        #设置log记录等级为info
        LogLog.setWholeLogLevel( 3 )
        
        #实例模拟器
        self.tpSim = TPSim( 'tps', 1 )
        
        self.Runstatus = False
        self.StartLoad = False
        self.CaseWrongFlag = False
        self.HandleExceptionFlag = False
        self.HandleRunning = True
        self.RunQ = Queue.Queue()  #清空队列，以便继续使用
        
        self.AnalysisInfo = [0, ""]  #用于自动分析时的显示消息传递
        
        #清空以前空的异常记录
        excepthandle.ClearEmptyLogFile()
        #开启运行线程
        _thread = MThread( self.HandleOrder, () , "handleRunQ" )
#        _thread.isDaemon()
#        _thread.setDaemon( True )
#        _thread.start()
        _thread.StartThread()
        
        #开启检测线程
        _thread = MThread( self.HandleDog, () , "HandleDog" )
#        _thread.isDaemon()
#        _thread.setDaemon( True )
#        _thread.start()
        _thread.StartThread()
        
        #导入OMAPFORMAT
#         OMAPParser.importFormat( r'./TPConfig/OMAPFormat.xml' )
#         OMAPParser.importEnuDic( r'./TPConfig/Enumerate.xml' )
#         OMAPParser.initDecompressDll( r'./dll/decompress.dll' )
#         OMAPParser.initZLIBDll( r'./dll/dgzDll.dll' )
        #导入已有的OMAPFigureConfig
        OMAPFigureConfigHandle.importOMAPFigureFile( r'./TPConfig/OMAPFigureConfig.xml' )
        #设置默认路径的path
        CaseParser.importLastConfig( r'./TPConfig/LastPlatformConfig.xml' )
        CaseParser.importPlatformInfo( r'./TPConfig/PlatformInfo.xml' )
        _workpath = CaseParser.getLastConfig_CaseVersion() if \
                    os.path.exists( CaseParser.getLastConfig_CaseVersion() ) else u"\被测版本标签号" 
        self.SetCurTestWorkSpace( _workpath )
        
        _mappath = CaseParser.getLastConfig_MapLib() if \
                   os.path.exists( CaseParser.getLastConfig_MapLib() ) else u"\Bcode_CC_OFFLINE_VN_Build20111223" 

        self.SetCurMapPath( _mappath )
        self.GetUpLoadConfig( r"./configfile/upload_config.xml" )
        
        self._mgr = aui.AuiManager()
        
        # tell AuiManager to manage this frame
        self._mgr.SetManagedWindow( self )

        # set frame icon
        self.SetIcon( images.Mondrian.GetIcon() )

        # set up default notebook style
        self._notebook_style = aui.AUI_NB_DEFAULT_STYLE | aui.AUI_NB_TAB_EXTERNAL_MOVE | wx.NO_BORDER
        self._notebook_theme = 0
        # Attributes
        self._textCount = 1
        self._transparency = 255
        self._snapped = False
        self._custom_pane_buttons = False
        self._custom_tab_buttons = False
        self._pane_icons = False

        #self.CreateStatusBar()
        #self.GetStatusBar().SetStatusText("Ready")

        self.CreateMenuBar()
        self.CreateStatusBar()
        self.StatusBarIni()
        self.Bind( wx.EVT_IDLE, self.OnIdle )
        self.BuildPanes()
        self.BindEvents()
        
        self.deviceGridDic = {}
        
        self.dis_timer = wx.PyTimer( self.interfaceCycleUpdata )
        self.Editing = False
        self.dis_timer.Start( 1000 ) #保证效率刷新率降低
        
   
    #--------------------------------------------------------------------------------
    #处理发送过来的顺序函数,都是用例运行相关函数，保证单一用例的执行，同时可以对出错用例进行相关的控制（重新执行等等）
    #--------------------------------------------------------------------------------
    def HandleOrder( self ):
        "handle order from RunQ"
        self.CaseWrongFlag = False
        while self.HandleRunning:
#             try:
                _handle, _para = self.RunQ.get()
                if True == self.CaseWrongFlag:#异常问题
                    #直接处理下一个用例,其他都不执行
                    if _handle in [self.test_config_panel.SetCurSelectCaseIndex, self.LoadCase]:
                        while self.HandleExceptionFlag:
                            time.sleep( 0.5 )
                        self.CaseWrongFlag = False
                        _handle( *_para )
                else:
                    #开始处理
                    if False == _handle( *_para ):
                        break                   
        print "End handle order."
    
    #-------------------------------------------------------------------
    #@实时检测系统的状态发现问题则立即重启系统
    #-------------------------------------------------------------------
    def HandleDog( self ):
        "handle order from RunQ"
        _WaitIndex = 0
        while self.HandleRunning:
            try:
                _errortype = excepthandle.LogException()
#                 print "HandleDog", _errortype
                if True == self.CaseWrongFlag:
                    #每个步骤只处理最前的一条：只需要重启一次就行了，CaseWrongFlag在出现错误并没有进行到下一个用例的时候将一直是True
                    continue
                    
                if 1 == _errortype or 4 == _errortype:#第一类和第4类错误需要重新启动用例
                    self.HandleExceptionFlag = True
                    self.CaseWrongFlag = True
                    #重新启动HandleOrder
                    self.logLog( "有异常情况，重新启动下位机," + "ErrorType:" + str( _errortype ) )                    
                    excepthandle.EndCurCaseThread( self )
#                     print "HandleDog:", _errortype
                    #初始化值
                    _WaitIndex = 0
                    self.Runstatus = False       
                    self.StartLoad = False
                    self.HandleExceptionFlag = False
                elif 2 == _errortype:
                    pass
                elif 3 == _errortype:
                    pass                                    
                
#                print "_WaitIndex", _WaitIndex
                time.sleep( 1 )
                if True == self.Runstatus and True == self.StartLoad:
                    _WaitIndex = _WaitIndex + 1
                else:
                    _WaitIndex = 0
                    
                if _WaitIndex > 600: #最多等10分钟
                    self.logLog( "有异常情况，重新启动下位机" )
#                    self.tpSim.ReBootHardWare( self.logLog )#这里应该是要硬件重启，同时重新执行本用例
                    _WaitIndex = 0
            except AttributeError, e:
#                print e
                _WaitIndex = 0
#                if self.tpSim.deviceRunstart:
#                    pass
        print "End HandleDog!"    
              
    def CreateMenuBar( self ):
        
        # create menu
        _mb = wx.MenuBar()
        
        #file menu
        _file_menu = wx.Menu()
        _Mu_NTC = _file_menu.Append( wx.NewId(), "New Test Case" )
        _Mu_ATCTW = _file_menu.Append( wx.NewId(), "Add Test Case to workstation" )
        _Mu_SWCWS = _file_menu.Append( wx.NewId(), "Switch Case Work Station" )
        _Mu_SWMP = _file_menu.Append( wx.NewId(), "Switch Map Path" )
#        _Mu_DTC = _file_menu.Append( wx.NewId(), "delete Test Case" )
#        _Mu_STC = _file_menu.Append( wx.NewId(), "Save Test Case" )
#        _Mu_SA = _file_menu.Append( wx.NewId(), "Save as" )
        _file_menu.AppendSeparator()
        _Mu_Exit = _file_menu.Append( wx.NewId(), "Exit" )

        #Operator
        _operator_menu = wx.Menu()
        _Mu_LC = _operator_menu.Append( wx.NewId(), "Load Case" )
        _Mu_RC = _operator_menu.Append( wx.NewId(), "Run Case" )
        _Mu_Running = _operator_menu.Append( wx.NewId(), "Running" )
        _Mu_EC = _operator_menu.Append( wx.NewId(), "End Case" )
        _Mu_RAC = _operator_menu.Append( wx.NewId(), "Run All Case" )
        
        #View
        _view_menu = wx.Menu()
        _Mu_SL = _view_menu.Append( wx.NewId(), "Show Log" )
        _Mu_SCT = _view_menu.Append( wx.NewId(), "Show Config Tree" )
        _Mu_STS = _view_menu.Append( wx.NewId(), "Show Train Status" )
#        _Mu_SOS = _view_menu.Append( wx.NewId(), "Show OMAP Status" )
        
        _setting_menu = wx.Menu()
        _Mu_OMAPCFG = _setting_menu.Append( wx.NewId(), "OMAP Configuration" )
        _Mu_TLTFTPCFG = _setting_menu.Append( wx.NewId(), "Telnet&FTP Configuration " )
        _Mu_DEVVARCFG = _setting_menu.Append( wx.NewId(), "Device Variant Configuration" )
        _Mu_DEVMSGCFG = _setting_menu.Append( wx.NewId(), "Device Message Configuration" )

        #Setting
        _view_menu = wx.Menu()
        _Mu_SL = _view_menu.Append( wx.NewId(), "Show Log" )
        _Mu_SCT = _view_menu.Append( wx.NewId(), "Show Config Tree" )
        _Mu_STS = _view_menu.Append( wx.NewId(), "Show Train Status" )
#        _Mu_SOS = _view_menu.Append( wx.NewId(), "Show OMAP Status" )
        
        #Help
        _help_menu = wx.Menu()
        _Mu_Help = _help_menu.Append( wx.NewId(), "Help" )
        
        _mb.Append( _file_menu, "&File" )
        _mb.Append( _operator_menu, "&Operator" )
        _mb.Append( _view_menu, "&View" )
        _mb.Append( _setting_menu, "&Setting" )
        _mb.Append( _help_menu, "&Help" )

        self.SetMenuBar( _mb )
        
        #邦定事件
        self.Bind( wx.EVT_MENU, self.NewTestCase, _Mu_NTC )
        self.Bind( wx.EVT_MENU, self.AddTestCase, _Mu_ATCTW )
        self.Bind( wx.EVT_MENU, self.SwitchCasePath, _Mu_SWCWS )
        self.Bind( wx.EVT_MENU, self.SwitchMapPath, _Mu_SWMP )
#        self.Bind( wx.EVT_MENU, self.DelTestCase, _Mu_DTC )
#        self.Bind( wx.EVT_MENU, self.SaveTestCase, _Mu_STC )
#        self.Bind( wx.EVT_MENU, self.SaveAsTestCase, _Mu_SA )
        self.Bind( wx.EVT_MENU, self.OnExit, _Mu_Exit )
        
        self.Bind( wx.EVT_MENU, self.OnLoad, _Mu_LC )
        self.Bind( wx.EVT_MENU, self.OnRun, _Mu_RC )
        self.Bind( wx.EVT_MENU, self.OnRunning, _Mu_Running )
#         self.Bind( wx.EVT_MENU, self.OnEnd, _Mu_EC )
        self.Bind( wx.EVT_MENU, self.OnRunAll, _Mu_RAC )

        self.Bind( wx.EVT_MENU, self.OnOMAPConfig, _Mu_OMAPCFG )
        self.Bind( wx.EVT_MENU, self.OnTelnetFTPConfig, _Mu_TLTFTPCFG )
        self.Bind( wx.EVT_MENU, self.OnDevVarConfig, _Mu_DEVVARCFG )
        self.Bind( wx.EVT_MENU, self.OnDevMsgCFG, _Mu_DEVMSGCFG )
        
        self.Bind( wx.EVT_MENU, self.ShowLog, _Mu_SL )
        self.Bind( wx.EVT_MENU, self.ShowCaseTree, _Mu_SCT )
        self.Bind( wx.EVT_MENU, self.ShowTrainStatus, _Mu_STS )
#        self.Bind( wx.EVT_MENU, self.ShowLog, _Mu_SOS )
        
        self.Bind( wx.EVT_MENU, self.OnHelp, _Mu_Help )
  
    #------------------------------------------------------
    #空闲的时候刷新下界面
    #------------------------------------------------------
    def OnIdle( self, event ):
        "刷新界面"
        #fresh test config panel
        self.new_config_panel_size = self.test_config_panel.GetSize()
        if self.old_config_panel_size != self.new_config_panel_size:  
            self.test_config_panel.Resize()
            self.old_config_panel_size = self.new_config_panel_size
        
    def OnOMAPConfig( self, event ):
        "On OMAP Config"
    
    def OnTelnetFTPConfig( self, event ):
        "On Telnet FTP Config"
        
    def OnDevVarConfig( self, event ):
        "On Device variant config"
        self.logLog( "Device Variant Config" )
        _DevFrame = devicecfgframe.DeviceCfgFrame( None, -1, "Device Choose", style = wx.DEFAULT_FRAME_STYLE )
        _DevFrame.Show( True )

    
    def OnDevMsgCFG( self, event ):
        "On Device Message config"
        self.logLog( "Device Message Config" )
        _DevMsgFrame = devicemsgcfgframe.DeviceMsgCfgFrame( None, -1, "Device Choose", style = wx.DEFAULT_FRAME_STYLE )
        _DevMsgFrame.Show( True )
    
    #-------------------------------------------------------
    #@处理函数，待添加
    #-------------------------------------------------------
    def NewTestCase( self, event ):
        self.logLog( "NewTestCase" )
#        _tmpplot = simpleplot.DataPlot( self )
#        _tmpplot.plot( [0, 1, 2, 3], [1, 2, 3, 4], "fads", "r--", ["x", "Y"] )
#        self._mgr.AddPane( _tmpplot, aui.AuiPaneInfo().
#                          Caption( "Wizard" ).
#                          Float().FloatingPosition( self.GetStartPosition() ).
#                          FloatingSize( wx.Size( 800, 480 ) ).MinimizeButton( True ) )
#        self._mgr.Update()
        _wizard = simplewizard.CaseWizard( self )

        if _wizard.StartWizard():
            wx.MessageBox( "Wizard completed successfully", "That's all folks!" )
            if True == _wizard.CreateNew: #需要更新CaseTree表
                self.UpDataCaseTree()
        else:
            wx.MessageBox( "Wizard was cancelled", "That's all folks!" )
        
        _wizard.Destroy()  
    
    def UpDataCaseTree( self ):
        "updata case tree"
        try:
            self.treenotebook.trees['CaseTree'].CreateTreeFromCaseNode()
        except:
            print "UpDataCaseTree error"
            
    
    def AddTestCase( self, event ):
        "Add Select Test Cases to work space"
        _Selectcase = self.treenotebook.getSelectCaseItem()
        #重新初始化选中的CaseInfo
        CaseParser.InitCurselectCaseInfo( _Selectcase )
        #重新更新用例界面的设置
        self.test_config_panel.RefreshPanelData()
        
#        dlg = wx.DirDialog(self, "Choose a Case directory:",
#                          style = wx.DD_DEFAULT_STYLE
#                           | wx.DD_DIR_MUST_EXIST
#                           | wx.DD_CHANGE_DIR
#                           )
#
#        if dlg.ShowModal() == wx.ID_OK:
#        
#            self.logLog('You selected: %s\n' % dlg.GetPath())
#
#        dlg.Destroy()
#        useMetal = False
#        if 'wxMac' in wx.PlatformInfo:
#            useMetal = self.cb.IsChecked()
#        dlg = simplecontrol.AddCasePanel( self, -1, "Add Case Dialog", size = ( 450, 200 ),
#                         #style=wx.CAPTION | wx.SYSTEM_MENU | wx.THICK_FRAME,
#                         style = wx.DEFAULT_DIALOG_STYLE, # & ~wx.CLOSE_BOX,
#                         useMetal = useMetal,
#                         )
#        if dlg.ShowModal() == wx.ID_OK:
#            _data = dlg.getDialogData()
#            if None != _data:
#                self.test_config_panel.addNewItem( _data[0], _data[1:] )
#        dlg.Destroy()        
    def SwitchCasePath( self, event ):
        "switch case path"
        _path = None
        _workpath = CaseParser.getLastConfig_CaseVersion() if \
                    os.path.exists( CaseParser.getLastConfig_CaseVersion() ) else\
                    os.path.join( os.getcwd(), u"被测版本标签号" )  
        print    _workpath   
        _dlg = wx.DirDialog( self,
                             message = "Choose Case Work Station Folder:",
                             #defaultPath = os.getcwd(),
                             defaultPath = _workpath,
                             style = wx.DD_DEFAULT_STYLE )
        if _dlg.ShowModal() == wx.ID_OK:
            _path = _dlg.GetPath()
            self.SetCurTestWorkSpace( _path )
            self.logLog( "Select Case Work Station Path: %s" % _path )
            self.test_config_panel.setCustable( [["NoCase", "NoCase", "NoCase", "NoCase"], ] )
            self.UpDataCaseTree()
            #可能还需要对相关数据的进行清空操作CaseParser，现在先不添加
            
        _dlg.Destroy()
        
    
    def SwitchMapPath( self, event ):
        "switch Map Path"
        _path = None
        _mappath = CaseParser.getLastConfig_MapLib() if \
                   os.path.exists( CaseParser.getLastConfig_MapLib() ) else\
                   os.path.join( os.getcwd(), u"Bcode_CC_OFFLINE_VN_Build20111223" )
        
        _dlg = wx.DirDialog( self,
                             message = "Choose Map Path Folder:",
#                             defaultPath = os.getcwd(),
                             defaultPath = _mappath,
                             style = wx.DD_DEFAULT_STYLE )
        if _dlg.ShowModal() == wx.ID_OK:
            _path = _dlg.GetPath()
            self.SetCurMapPath( _path )
            self.logLog( "Select  Map Path: %s" % _path )
        _dlg.Destroy()
        
    def DelTestCase( self, event ):
        pass
    
    def SaveTestCase( self, event ):
        pass

    def SaveAsTestCase( self, event ):
        pass
        
    def ShowLog( self, event ):
        "show log"
        self._mgr.GetPane( "Log_Text" ).Show().Bottom().Layer( 0 ).Row( 0 ).Position( 0 )
        self._mgr.Update()
    
    def ShowTrainStatus( self, event ):
        "show train status"
        self._mgr.GetPane( "ShowStatusPanel" ).Show().Right().Layer( 0 ).Row( 0 ).Position( 0 )
        self._mgr.Update()

    def ShowCaseTree( self, event ):
        "show case tree"
        self._mgr.GetPane( "Config_Tree" ).Show().Left().Layer( 0 ).Row( 0 ).Position( 0 )
        self._mgr.Update()        
        
    def OnHelp( self, event ):
        _DevFrame = devicecfgframe.VersionFrame( None, -1, "Version Information", style = wx.DEFAULT_FRAME_STYLE, size = ( 300, 50 ) )
        _DevFrame.Show( True )        
    
    def BuildPanes( self ):

        # min size for the frame itself isn't completely done.
        # see the end up AuiManager.Update() for the test
        # code. For now, just hard code a frame minimum size
        self.SetMinSize( wx.Size( 800, 600 ) )

        # prepare a few custom overflow elements for the toolbars' overflow buttons

        prepend_items, append_items = [], []
        item = aui.AuiToolBarItem()
        
        item.SetKind( wx.ITEM_SEPARATOR )
        append_items.append( item )

        item = aui.AuiToolBarItem()        
        item.SetKind( wx.ITEM_NORMAL )
        item.SetId( wx.NewId() )
        item.SetLabel( "Customize..." )
        append_items.append( item )

        self.ToolBarDic = {}
        # create some toolbars
        #File tb
        _tb_File = aui.AuiToolBar( self, -1, wx.DefaultPosition, wx.DefaultSize,
                            aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_OVERFLOW )
        _tb_File.SetToolBitmapSize( wx.Size( 32, 32 ) )
        self.ToolBarDic["File"] = _tb_File
        _tb_FILE_AECTW = _tb_File.AddSimpleTool( wx.NewId(), "tb_Add_Exist_Case_to_workstation", \
                                                wx.Bitmap( u"interface/ico/add_exist.ico", wx.BITMAP_TYPE_ANY ), \
                                                "Add Exist Case to workstation" )
        _tb_File.SetCustomOverflowItems( prepend_items, append_items )
        _tb_File.Realize()        
        
        #operator tb
        _tb_Operator = aui.AuiToolBar( self, -1, wx.DefaultPosition, wx.DefaultSize,
                            aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_OVERFLOW )
        _tb_Operator.SetToolBitmapSize( wx.Size( 32, 32 ) )
        self.ToolBarDic["Operator"] = _tb_Operator
        _tb_Operator_Load = _tb_Operator.AddSimpleTool( wx.NewId(), "tb_Load", \
                                                       wx.Bitmap( u"interface/ico/load.ico", wx.BITMAP_TYPE_ANY ), \
                                                       "Load Case" )
        _tb_Operator_Run = _tb_Operator.AddSimpleTool( wx.NewId(), "tb_Run", \
                                                      wx.Bitmap( u"interface/ico/run.ico", wx.BITMAP_TYPE_ANY ), \
                                                      "Run Case" )
        
        _tb_Operator_Running = _tb_Operator.AddSimpleTool( wx.NewId(), "tb_Running", \
                                                      wx.Bitmap( u"interface/ico/run.png", wx.BITMAP_TYPE_ANY ), \
                                                      "Run Case" )
        
#         _tb_Operator_End = _tb_Operator.AddSimpleTool( wx.NewId(), "tb_df", \
#   													  wx.Bitmap( u"interface/ico/help.ico", wx.BITMAP_TYPE_ANY ), \
#   													  "Eddnd Case" )
        _tb_Operator.SetCustomOverflowItems( prepend_items, append_items )
        _tb_Operator.Realize()

        
        #Variant display tool bar
        _tb_Var_Dis = aui.AuiToolBar( self, -1, wx.DefaultPosition, wx.DefaultSize,
                            aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_OVERFLOW )
        _tb_Var_Dis.SetToolBitmapSize( wx.Size( 32, 32 ) )
        self.ToolBarDic["Var_Display"] = _tb_Var_Dis
        self.ToolBarDic["Var_Display_Button"] = {}
        self.ToolBarDic["Var_Display_Button"]["Edit_bmp"] = wx.Bitmap( u"interface/ico/Start.png", wx.BITMAP_TYPE_ANY )   
        self.ToolBarDic["Var_Display_Button"]["Edit_OK_bmp"] = wx.Bitmap( u"interface/ico/Edit_OK.ico", wx.BITMAP_TYPE_ANY )   
        self.ToolBarDic["Var_Display_Button"]["Refresh_bmp"] = wx.Bitmap( u"interface/ico/refresh.ico", wx.BITMAP_TYPE_ANY )   
        self.ToolBarDic["Var_Display_Button"]["UnRefresh_bmp"] = wx.Bitmap( u"interface/ico/stop_refresh.ico", wx.BITMAP_TYPE_ANY ) 
        
        self.ToolBarDic["Var_Display_Button"]["up"] = wx.Bitmap( u"interface/ico/up.png", wx.BITMAP_TYPE_ANY )             
        self.ToolBarDic["Var_Display_Button"]["down"]=wx.Bitmap(u"interface/ico/down.png",wx.BITMAP_TYPE_ANY)
        _tb_Var_Dis_Edit = _tb_Var_Dis.AddSimpleTool( wx.NewId(), "_tb_Var_Dis_Edit", \
                                               self.ToolBarDic["Var_Display_Button"]["Edit_bmp"], \
                                               "Variant Edit" )
        _tb_Var_Dis_Refresh = _tb_Var_Dis.AddSimpleTool( wx.NewId(), "_tb_Var_Dis_Refresh", \
                                               self.ToolBarDic["Var_Display_Button"]["UnRefresh_bmp"], \
                                               "Stop Refresh" )
        _tb_Var_Dis_Refresh = _tb_Var_Dis.AddSimpleTool( wx.NewId(), "_tb_Var_Dis_Refresh", \
                                               self.ToolBarDic["Var_Display_Button"]["up"], \
                                               "Speed up" )
        _tb_Var_Dis_Refresh = _tb_Var_Dis.AddSimpleTool( wx.NewId(), "_tb_Var_Dis_Refresh", \
                                               self.ToolBarDic["Var_Display_Button"]["down"], \
                                               "Slow down" )
              
        #将上面两个按钮添加到类变量中，以便操作
        self.ToolBarDic["Var_Display_Button"]["Edit"] = _tb_Var_Dis_Edit  
        _tb_Var_Dis.Realize()
        
        self.treenotebook = cuscontrol.TreeNotebook( self, ( 300, 300 ) )        
        self._mgr.AddPane( self.treenotebook, aui.AuiPaneInfo().Name( "Config_Tree" ).Caption( "Config Tree" ).
                          Left().BestSize( wx.Size( 300, 400 ) ).MinSize( wx.Size( 150, 400 ) ).CloseButton( False ).MaximizeButton( True ).
                          MinimizeButton( True ) )
        
        self.Bind( wx.EVT_TREE_ITEM_ACTIVATED, self.OnGenACTIVATED, self.treenotebook.trees["General"] )
        self.Bind( wx.EVT_TREE_ITEM_ACTIVATED, self.OnTPACTIVATED, self.treenotebook.trees["TPConfig"] )
        self.Bind( wx.EVT_TREE_ITEM_ACTIVATED, self.OnTestACTIVATED, self.treenotebook.trees["testconfig"] )
        
        self.Log = self.CreateTextCtrl( "" )
        self.Log.SetEditable( False )
        wx.Log_SetActiveTarget( MyLog( self.Log ) )
        self._mgr.AddPane( self.Log, aui.AuiPaneInfo().
                          Name( "Log_Text" ).Caption( "Log Message" ).Bottom().MinimizeButton( True ).CloseButton( False ) )
        # create some center panes
        self._mgr.AddPane( self.CreateNotebook(), aui.AuiPaneInfo().Name( "Notebook_content" ).
                          CenterPane().PaneBorder( False ) )
        
        #create show panel
        self.ShowStatusPanel = simplepanel.ShowStatusPanel( self, size = ( 600, 800 ) )
        self._mgr.AddPane( self.ShowStatusPanel, aui.AuiPaneInfo().Name( "ShowStatusPanel" ).Caption( "Status Panel" ).
                           Right().Layer( 1 ).Position( 1 ).
#                          Float().FloatingPosition( self.GetStartPosition() ).FloatingSize( wx.Size( 600, 800 ) ).
                           CloseButton( True ).MaximizeButton( True ).MinimizeButton( True ) )  
      
        
        # add the toolbars to the manager
        self._mgr.AddPane( _tb_File, aui.AuiPaneInfo().Name( "File" ).Caption( "File Toolbar" ).
                          ToolbarPane().Top().Row( 1 ) )
        self._mgr.AddPane( _tb_Operator, aui.AuiPaneInfo().Name( "Operator" ).Caption( "Operator Toolbar" ).
                          ToolbarPane().Top().Row( 1 ).Position( 1 ) )
#         self._mgr.AddPane( _tb_Analysis, aui.AuiPaneInfo().Name( "Analysis" ).Caption( "Analysis Toolbar" ).
#                           ToolbarPane().Top().Row( 1 ).Position( 2 ) )
        self._mgr.AddPane( _tb_Var_Dis, aui.AuiPaneInfo().Name( "VariantDisplay" ).Caption( "Operator Toolbar" ).
                          ToolbarPane().Top().Row( 1 ).Position( 3 ) )


        
        
        # make some default perspectives
        perspective_all = self._mgr.SavePerspective()

        all_panes = self._mgr.GetAllPanes()
        #先将所有的pane隐藏
        for pane in all_panes:
            if not pane.IsToolbar():
                pane.Hide()
        #显示指定的几个
        self._mgr.GetPane( "Config_Tree" ).Show().Left().Layer( 0 ).Row( 0 ).Position( 0 )
#        self._mgr.GetPane( "ShowStatusPanel" ).Show().Right().Layer( 0 ).Row( 0 ).Position( 0 )
        self._mgr.GetPane( "Log_Text" ).Show().Bottom().Layer( 0 ).Row( 0 ).Position( 0 )
        self._mgr.GetPane( "Notebook_content" ).Show()
        
        perspective_default = self._mgr.SavePerspective()

        self._perspectives = []
        self._perspectives.append( perspective_default )
        self._perspectives.append( perspective_all )

        self._nb_perspectives = []
        auibook = self._mgr.GetPane( "Notebook_content" ).window
        nb_perspective_default = auibook.SavePerspective()
        self._nb_perspectives.append( nb_perspective_default )
        
        self._mgr.LoadPerspective( perspective_default )
        
        #邦定事件
#         self.Bind( wx.EVT_TOOL, self.NewTestCase, _tb_FILE_ANCTW )
        self.Bind( wx.EVT_TOOL, self.AddTestCase, _tb_FILE_AECTW )
#         self.Bind( wx.EVT_TOOL, self.DelTestCase, _tb_FILE_DECFW )
#         self.Bind( wx.EVT_TOOL, self.SaveTestCase, _tb_FILE_SC )
#         self.Bind( wx.EVT_TOOL, self.SaveAsTestCase, _tb_FILE_SAC )

        self.Bind( wx.EVT_TOOL, self.OnStart, _tb_Var_Dis_Edit )
        self.Bind( wx.EVT_TOOL, self.OnStop, _tb_Var_Dis_Refresh )
        
        self.Bind( wx.EVT_TOOL, self.OnLoad, _tb_Operator_Load )
        self.Bind( wx.EVT_TOOL, self.OnRun, _tb_Operator_Run )
        self.Bind( wx.EVT_TOOL, self.OnRunning, _tb_Operator_Running )
#         self.Bind( wx.EVT_TOOL, self.OnEnd, _tb_Operator_End )
#         self.Bind( wx.EVT_TOOL, self.OnRunAll, _tb_Operator_RunAll )
        
#         self.Bind( wx.EVT_TOOL, self.OnHelp, _tb_Help_H )        
#         self.Bind( wx.EVT_TOOL, self.OnExit, _tb_Help_Exit )
#         self.Bind( wx.EVT_TOOL, self.OnAnalysis, _tb_Analysis_Start )
        
        # "commit" all changes made to AuiManager
        self._mgr.Update()

    def OnAnalysis( self, event ):
        "button Analysis"
        _max = len( CaseParser.getCurSelectCaseInfo() )
        if _max <= 0:
            return

        dlg = wx.ProgressDialog( "Analysis Progress dialog",
                                 "Start Analysis!",
                                 maximum = _max,
                                 parent = self,
                                 style = wx.PD_CAN_ABORT 
                                | wx.PD_APP_MODAL
                                | wx.PD_ELAPSED_TIME
                                | wx.PD_REMAINING_TIME
                                )
        self.AnalysisInfo = [0, ""]
        _Analysishandle = ( self.AnalysisCase, () )
        self.RunQ.put( _Analysishandle )
        
        while self.AnalysisInfo[0] < _max:
            time.sleep( 0.1 )
            dlg.Update( self.AnalysisInfo[0], self.AnalysisInfo[1] )
        dlg.Destroy() 
        
    
    def AnalysisCase( self ):
        "On analysis"
        self.logLog( u"Start Analysis!" )
        
        for _index in range( len( CaseParser.getCurSelectCaseInfo() ) ):
            self.AnalysisInfo[0] = _index + 1          
            self.test_config_panel.SetCurSelectCaseIndex( _index )
            _CaseInfo = CaseParser.getCurCaseInfo()
            _Ver = _CaseInfo[0]
            _CaseNum = _CaseInfo[1]
            _CaseStep = _CaseInfo[2]
            self.logLog( u"开始自动分析..." )
            self.logLog( "Version: " + _Ver + " Case: " + _CaseNum + " Step: " + _CaseStep )
            self.AnalysisInfo[1] = ( "Analysis:" + _CaseNum + " " + _CaseStep )[0:28] + "..."
            self.test_config_panel.SetCaseStatus( 5 )
            _path = CaseParser.getCurCasePath()
            #---------导入用例的配置-----------------
            CaseParser.importCurRunCaseConfig()
            _logpath = _path[0]
            _scriptpath = _path[1]
            _DownLogPath = _path[2]
#            print _scriptpath
#            try:
            _tmpAnalysis = ResultAnalysis()
            _tmpAnalysis.AnalysisInit( InitType = "All",
                                       binpath = CaseParser.getCurRunCaseMappath()[0],
                                       txtpath = CaseParser.getCurRunCaseMappath()[1],
                                       trainroutepath = _scriptpath + "/scenario/train_route.xml",
                                       analysispath = _scriptpath + "/analysis/autoAnalysis.xml",
                                       saveLogPath = _logpath + "/log/Analysis.log",
                                       omaplogpath = _DownLogPath #logfolder
                                            )
            _tmpAnalysis.startAnalysis()
            self.test_config_panel.SetCaseStatus( 6 )
#            except:
#                print "OnAnalysis Error!"
#                continue
        print 'AnalysisCase GC collect:', gc.collect()
        self.logLog( u"Analysis end!" )    
        return True        
        
    
    def OnStart( self, event ):
        
        if Car._manualStop == True:
            Car._manualStart = True
#             Car._carStop = False
#             Car._manualStop = False
            print '---------------------------------on start----------------------------'
        #首先更改图标
#         tool = self.ToolBarDic["Var_Display_Button"]["Edit"]
#         
#         if tool.bitmap != self.ToolBarDic["Var_Display_Button"]["Edit_bmp"]:
#             tool.bitmap = self.ToolBarDic["Var_Display_Button"]["Edit_bmp"]
#             self.Editing = False
#             tool.short_help = "Edit"
#         else:
#             tool.bitmap = self.ToolBarDic["Var_Display_Button"]["Edit_OK_bmp"]
#             self.Editing = True
#             tool.short_help = "Stop Edit"
#         
#         self.ToolBarDic["Var_Display"].Refresh()
        
#         app = wx.App(0)
#         frame = TrainSimulator(None,-1)     
#         frame.Show(True)
#         app.MainLoop()
        pass
        
    def OnStop( self, event ):
        if Car._allowstop == True:
            Car._manualStop = True
            Car._manualStart = False
#             time.sleep(0.02)
#             Car._manualStop = False
#             Car._manualStart = True
        
        #首先更改图标
#         tool = self.ToolBarDic["Var_Display_Button"]["Refresh"]
#         
#         if tool.bitmap != self.ToolBarDic["Var_Display_Button"]["Refresh_bmp"]:
#             tool.bitmap = self.ToolBarDic["Var_Display_Button"]["Refresh_bmp"]
#             self.dis_timer.Stop()
#             tool.short_help = "Refresh"
#         else:
#             tool.bitmap = self.ToolBarDic["Var_Display_Button"]["UnRefresh_bmp"]
#             self.dis_timer.Start( 100 )
#             tool.short_help = "Stop Refresh"
#         self.ToolBarDic["Var_Display"].Refresh()
        pass

    def OnGenACTIVATED( self, event ):
        self.logLog( self.treenotebook.trees["General"].GetItemText( event.GetItem() ) )
        _PageName = self.treenotebook.trees["TPConfig"].GetItemText( event.GetItem() ) 
        
        if _PageName == 'Train status':
            self._mgr.GetPane( "ShowStatusPanel" ).Show().Right().Layer( 0 ).Row( 0 ).Position( 0 )
            self._mgr.Update()
        elif _PageName == 'OMAP status':
            for _index in range( self.notbook_ctrl.GetPageCount() ):
                if _PageName == self.notbook_ctrl.GetPageText( _index ): #有则不添加
#                    _hasPage = True
                    return
#            _hasPage = False
#            for _Name in self.deviceGridDic:
#                if _PageName == _Name:
#                    _hasPage = True
#                    break 
                
#            if False == self.deviceGridDic.has_key( _PageName ):
            #没有的已经销毁掉了
#            print self.deviceGridDic
            self.deviceGridDic[_PageName] = cuscontrol.OMAPAttrGrid( self )
                 
            #无则添加
            self.notbook_ctrl.AddPage( self.deviceGridDic[_PageName], _PageName, False )
            self.deviceGridDic[_PageName].Resize()
            self.deviceGridDic[_PageName].Refresh()
            self.deviceGridDic[_PageName].Update()
                        
        event.Skip

    def OnTPACTIVATED( self, event ):
        self.logLog( self.treenotebook.trees["TPConfig"].GetItemText( event.GetItem() ) )
        event.Skip
        
    def OnTestACTIVATED( self, event ):
        _device = self.treenotebook.trees["testconfig"].GetItemText( event.GetItem() )
        self.logLog( "select " + _device )
        #生成与设备对应的grid
        #事先还需要进行判断
#        _hasPage = False
        for _index in range( self.notbook_ctrl.GetPageCount() ):
            if _device == self.notbook_ctrl.GetPageText( _index ): #有则不添加
#                _hasPage = True
                return
        
#        _hasPage = False
#        for _Name in self.deviceGridDic:
#            if _device == _Name:
#                _hasPage = True
#                break 
        
#        if False == self.deviceGridDic.has_key( _device ):
        print "OnTestACTIVATED", self.deviceGridDic
        self.deviceGridDic[_device] = cuscontrol.DeviceAttrGrid( self, self.tpSim.loadDeviceDic[_device] )
             
        #无则添加
        self.notbook_ctrl.AddPage( self.deviceGridDic[_device], _device, False )
        self.deviceGridDic[_device].Resize()
        self.deviceGridDic[_device].Refresh()
        self.deviceGridDic[_device].Update()

        event.Skip
            
    def BindEvents( self ):
        "bind events"
        self.Bind( wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground )
        self.Bind( wx.EVT_SIZE, self.OnSize )
        self.Bind( wx.EVT_IDLE, self.OnIdle )
    
    #--------------------------------------------------------------
    #@用于处理提示信息的显示，显示在statusbar上
    #--------------------------------------------------------------
    def OnShowInfo( self, event ):
        
        _name = event.GetEventObject().GetName()
        self.GetStatusBar().StatusSetText( _name )
        event.Skip

    #--------------------------------------------------------------
    #@用于处理提示信息的显示，显示在statusbar上
    #--------------------------------------------------------------
    def OnKillInfo( self, event ):
        
        #_name = event.GetEventObject().GetName()
        self.GetStatusBar().StatusSetText( "" )
        event.Skip
    
    def DoUpdate( self ):

        self._mgr.Update()
        self.Refresh()


    def OnEraseBackground( self, event ):

        event.Skip()


    def OnSize( self, event ):

        event.Skip()


    def OnSettings( self, event ):

        # show the settings pane, and float it
        floating_pane = self._mgr.GetPane( "settings" ).Float().Show()

        if floating_pane.floating_pos == wx.DefaultPosition:
            floating_pane.FloatingPosition( self.GetStartPosition() )

        self._mgr.Update()

        

    def GetStartPosition( self ):

        x = 20
        pt = self.ClientToScreen( wx.Point( 0, 0 ) )
        return wx.Point( pt.x + x, pt.y + x )

    def EndRunningQ( self ):
        return False
        
    def OnExit( self, event ):
        self.HandleRunning = False
        #关闭所有socket
        self.tpSim.CloseAllSocket()
        _RunInfo = ( self.EndRunningQ, () )
        self.RunQ.put( _RunInfo )

        time.sleep( 6 )
        #关闭异常记录
        excepthandle.LogClose()
        
        print 'cur threading %d' % ( threading.activeCount() )
        for _t in threading.enumerate():
            print 'thread name:', _t.getName()        
        self.Destroy()
        self.Close( True )


    def CreateTextCtrl( self, ctrl_text = "" ):
        return wx.TextCtrl( self, -1, ctrl_text, wx.Point( 0, 0 ), wx.Size( 150, 90 ),
                           wx.NO_BORDER | wx.TE_MULTILINE )

#    def CreateSizeReportCtrl(self, width = 80, height = 80):
#
#        ctrl = simplecontrol.SizeReportCtrl(self, -1, wx.DefaultPosition, wx.Size(width, height), self._mgr)
#        return ctrl

    def CreateNotebook( self ):

        # create the notebook off-window to avoid flicker
        client_size = self.GetClientSize()
        self.notbook_ctrl = aui.AuiNotebook( self, -1, wx.Point( client_size.x, client_size.y ),
                              wx.Size( 430, 200 ), self._notebook_style )

        arts = [aui.AuiDefaultTabArt, aui.AuiSimpleTabArt, aui.VC71TabArt, aui.FF2TabArt,
                aui.VC8TabArt, aui.ChromeTabArt]

        art = arts[self._notebook_theme]()
        self.notbook_ctrl.SetArtProvider( art )

        _page_bmp = wx.ArtProvider.GetBitmap( wx.ART_NORMAL_FILE, wx.ART_OTHER, wx.Size( 16, 16 ) )
        self.test_config_panel = cuscontrol.TestConfig( self.notbook_ctrl, self.notbook_ctrl.Size )
        self.notbook_ctrl.AddPage( self.test_config_panel, "test config", False, _page_bmp )
        
        #邦定事件
        self.Bind( wx.EVT_SIZE, self.updataNotebookSize, self ) #用于更新窗口的大小
        self.Bind( wx.EVT_SIZING, self.updataNotebookSize, self ) #用于更新窗口的大小
        self.Bind( aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.OnPageChange, self.notbook_ctrl )    
        self.Bind( aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.OnPageClose, self.notbook_ctrl )    
        
        return self.notbook_ctrl
    
    
    #---------------------------------------------------------------
    #用于处理需要周期刷新的数据，主要是界面中个设备的variant刷新，以及其他界面
    #---------------------------------------------------------------
    def interfaceCycleUpdata( self ):
        "Interface cycle updata"
        #设备显示更新
        if self.Editing or self.Runstatus == False: #在编辑的时候，不进行刷新
            return
        for _key in self.deviceGridDic:
#            print "da", self.deviceGridDic
            if self.deviceGridDic[_key]: #页面还存在
#                print "da1", self.deviceGridDic
                self.deviceGridDic[_key].updataGrid() 
                self.deviceGridDic[_key].Resize()
                self.deviceGridDic[_key].Refresh()       
        
        self.ShowStatusPanel.upDataCaseInfo()
#         self.ShowStatusPanel.upDataOMAPInfo()
        self.ShowStatusPanel.updataTPSInfo( self.tpSim )
        self.ShowStatusPanel.Refresh()
#            print "error message"
    
    #----------------------------------------------------------------
    #NoteBook关闭页面的时候处理的事件
    #----------------------------------------------------------------
    def OnPageClose( self, event ):
        self.logLog( "OnPageClose" )
        self.logLog( str( event.GetSelection() ) )
        if event.GetSelection() < 0:
            return
        
        if self.test_config_panel != self.notbook_ctrl.GetPage( event.GetSelection() ):
            #disable Toobar
            self.ToolBarDic["File"].Enable( False )
            self.ToolBarDic["Operator"].Enable( False )
            
        elif self.test_config_panel == self.notbook_ctrl.GetPage( event.GetSelection() ):
            #启动Toolbar
            self.ToolBarDic["File"].Enable( True )
            self.ToolBarDic["Operator"].Enable( True )

    #-----------------------------------------------------------------
    #@用于处理Page变化时的ToolbarEnabel的相关处理
    #-----------------------------------------------------------------
    def OnPageChange( self, event ):
        #print dir(event)
        #print self.notbook_ctrl.GetPage(event.GetOldSelection())
        self.logLog( str( event.GetSelection() ) )
        if event.GetSelection() < 0:
            return
        
        if self.test_config_panel != self.notbook_ctrl.GetPage( event.GetSelection() ):
            #disable Toobar
            self.ToolBarDic["File"].Enable( False )
            self.ToolBarDic["Operator"].Enable( False )
            
        elif self.test_config_panel == self.notbook_ctrl.GetPage( event.GetSelection() ):
            #启动Toolbar
            self.ToolBarDic["File"].Enable( True )
            self.ToolBarDic["Operator"].Enable( True )
            
    def updataNotebookSize( self, event ):
        "更新nobook的大小，同时调整期中的test_config_panel中的grid的大小"
        self.test_config_panel.Resize()
        self.test_config_panel.Refresh()
        self.test_config_panel.Update()
        #self.logLog('updataNotebookSize')


    def logLog( self, logStr ):
        logs = commlib.curTime()+ ' --- ' + logStr
        wx.LogMessage( logs )

    #-----------------------------------------------------------------------
    #@界面状态栏相关操作
    #-----------------------------------------------------------------------
    def StatusBarIni( self ):
        _statusbar = self.GetStatusBar()
        # This status bar has three fields
        _statusbar.SetFieldsCount( 2 )
        # Sets the three fields to be relative widths to each other.
        _statusbar.SetStatusWidths( [-1, -1] )
        # Field 0 ... just text
        _statusbar.SetStatusText( "Welcome to test platform!", 0 )
        # We're going to use a timer to drive a 'clock' in the last field.
        self.timer = wx.PyTimer( self.statusbarNotify )
        self.timer.Start( 1000 )
        self.statusbarNotify()
    
    #---------------------------------------------------------------
    #用于显示一些提示信息在statusbar上
    #---------------------------------------------------------------
    def StatusSetText( self, str ):
        self.GetStatusBar().SetStatusText( str )

    #----------------------------------------------------------------
    #@设定本次用例的总目录
    #----------------------------------------------------------------
    def SetCurTestWorkSpace( self, path ):
        "set current test work space"
        self.__CurTestWorkSpace = path
        CaseParser.LoadCaseFolder( path )
        CaseParser.setLastConfig_CaseVersion( r'./TPConfig/LastPlatformConfig.xml' , path )
        #还需要更新tree以及相关的其他
        
    #----------------------------------------------------------------
    #@设定地图库的总目录
    #----------------------------------------------------------------
    def SetCurMapPath( self, path ):
        "set current map work space"
        self.__CurMapPath = path
        CaseParser.LoadMapFolder( path )
        CaseParser.setLastConfig_MapLib( r'./TPConfig/LastPlatformConfig.xml' , path )
        
    #---------------------------------------------------------------
    #@载入上传配置文件的config
    #---------------------------------------------------------------
    def GetUpLoadConfig( self, path ):
        "get upload configuration."
        CaseParser.importUpLoadConfig( path )
    
    #-----------------------------------------------------------------
    #@用于处理toolbar中的按钮的enable
    #----------------------------------------------------------------
    def HanderToolBar( self, event ):
        "hander Tool bar Enable"
        self.logLog( "-------------------------" )
    
    def ImportCases( self, path ):
        "import cases from path."
        self.Cases = None
        
    #-----------------------------------------------------------------
    #@用于statusbar显示的函数
    #-----------------------------------------------------------------
    def statusbarNotify( self ):
        t = time.localtime( time.time() )
        st = time.strftime( "%d-%b-%Y   %I:%M:%S", t )
        self.GetStatusBar().SetStatusText( st, 1 )

    def OnLoad( self, event ):
        "button load"
        _RunInfo = ( self.LoadCase, () )
        self.RunQ.put( _RunInfo )
    
    def UpdataAllDevPage( self, devicelist ):
        "delete all device pages for another case start."
        for _index in range( self.notbook_ctrl.GetPageCount() ):
            _text = self.notbook_ctrl.GetPageText( _index )
            if _text in devicelist: #有时则更新对应的device
                self.deviceGridDic[_text].setDeviceNode( self.tpSim.loadDeviceDic[_text] )
        
    def LoadCase( self ):
        "load case"
        self.test_config_panel.Enable( False )
        print '--interface loadcase curIndex----',self.test_config_panel.curIndex
        if self.test_config_panel.curIndex == None or\
           self.test_config_panel.curIndex < 0:
            self.logLog( "please select a case to load" )
            return
#        #运行过程中不能编辑CaseTree
#        self.treenotebook.EnableCaseTree( False )
        #获取当前的脚本的路径
        _path = CaseParser.getCurCasePath()
        #初始化TPS
#        self.tpSim = TPSim( 'tps', 1 )
        self.tpSim.ReInitTPS()
        #---------导入用例的配置-----------------
        CaseParser.importCurRunCaseConfig()
                
        self.logLog( u"设备加载" )
        self.test_config_panel.SetCaseStatus( 1 )
        self.tpSim.deviceRunstart = False
        
        #先对路径进行拼接
        self.tpSim.joinDevInitPath( _path , CaseParser.getCurRunCaseTrainEnd() )
        
        #tps init
        self.tpSim.deviceInit( **self.tpSim.deviceInitPara['tps'] )
               
        for _d in self.tpSim.loadDeviceList:
            self.logLog( u"加载设备:" + _d )
        #print 'dev dic', self.tpSim.loadDeviceDic
        self.treenotebook.updataTestConfigTree( self.tpSim.getDeviceList() )
        self.UpdataAllDevPage( self.tpSim.getDeviceList() ) 
        self.Runstatus = True       
        self.StartLoad = True 
        #更新treeConfiglist中的设备
        self.StartLoad = False
        return True
    
    def OnRunning(self,event ):
        if Car._carStop == True:
            Car._carBrack = True
            pass
        pass
    
    def OnRun( self, event ):
        "button run"
        _RunInfo = ( self.RunCase, () )
        self.RunQ.put( _RunInfo )
    
    def RunCase( self ):
        "Run test case."
        self.logLog( u"设备运行" )
        #self.time1.Start(self.cycle)      #milliseconds
        self.test_config_panel.SetCaseStatus( 2 )
#         self.tpSim.telnet.StartSaveTelnetContent()
        #开始记录omap
#         self.tpSim.omap.OMAPRun()
        #开启线程，并运行
        self.tpSim.deviceRunstart = True
        self.tpSim.sendStartCommand = True
#         self.tpSim.createThread( self.tpSim.deviceRunthread, '', "sim_device_Run_thread" )
#         self.tpSim.getDataValue( 'sim_device_Run_thread' ).StartThread( "ABOVE_NORMAL" )
#         self.tpSim.createThread( self.tpSim.deviceSendMsg, '', "send_to_ccnv_thread" )
#         self.tpSim.getDataValue( 'send_to_ccnv_thread' ).StartThread( "ABOVE_NORMAL" )
        
        self.tpSim.createThread( self.tpSim.deviceSerialSendMsg, '', "send_to_sil2_thread" )
        self.tpSim.getDataValue( 'send_to_sil2_thread' ).StartThread( "ABOVE_NORMAL" )

        
        #定时发送周期更新消息
        self.tpSim.createThread( self.tpSim.SendDeviceUpdateMessage, '', "Send_Device_UpdataMsg" )
        self.tpSim.getDataValue( 'Send_Device_UpdataMsg' ).StartThread( "ABOVE_NORMAL" )

#         self.tpSim.createThread( self.tpSim.SendCBKMsg, '', "send_cbk_Msg_thread" )
#         self.tpSim.getDataValue( 'send_cbk_Msg_thread' ).StartThread( "ABOVE_NORMAL" )   
        
        return True
                
    def OnEnd( self, event ):
        "button run"
        #self.time1.Stop()
        _RunInfo = ( self.EndCase, () )
        self.RunQ.put( _RunInfo )      
        
    def EndCase( self ):
        "End Case" 
        self.Runstatus = False 
#         self.tpSim.telnet.CloseTelnet()
#         self.tpSim.omap.OMAPEnd()
        time.sleep( 2 ) #保证已经无消息给上位机   
        self.tpSim.deviceRunstart = False    
        #发送结束发送消息给平台的发送队列
        self.tpSim.inQ.put( "END Case" )
        self.tpSim.deviceEnd()       
        print 'GC collect:', gc.collect()
        time.sleep( 5 ) 
        self.logLog( u"结束设备运行" )
        self.test_config_panel.SetCaseStatus( 3 )
         
#        #运行结束后开启CaseTree编辑选项
#        self.treenotebook.EnableCaseTree( True )
                 
        time.sleep( 20 ) #结束后要延时20秒等待所有线程结束
        print 'cur threading %d' % ( threading.activeCount() )
        for _t in threading.enumerate():
            print 'thread name:', _t.getName()
 
        self.test_config_panel.Enable( True ) 
        return True
        
    
    def OnRunAll( self, event ):
        "Run All"
        _RunInfo = ( self.RunAllCase, () )
        self.RunQ.put( _RunInfo )  
    
    def TimeSleep( self, sleeptime ):
        time.sleep( sleeptime )
        return True

    def SleepCaseRunTime( self ):
        time.sleep( CaseParser.getCurRunCaseConfig()['endconfig'][1] ) 
        return True
        
    def OnTimeSleep( self, time ): 
        _TimeInfo = ( self.TimeSleep, [time] )
        self.RunQ.put( _TimeInfo ) 

    def OnSleepCaseRunTime( self ):
        _TimeInfo = ( self.SleepCaseRunTime, () )
        self.RunQ.put( _TimeInfo ) 
        
    def OnChangeTCFGPanelIndex( self, index ):
        _ChangeInfo = ( self.test_config_panel.SetCurSelectCaseIndex, ( index, ) )
        self.RunQ.put( _ChangeInfo )           
        
    def OnShowRunLog( self, Str ):
        _ShowInfo = ( self.logLog, ( Str, ) )
        self.RunQ.put( _ShowInfo )         
    
    def RunAllCase( self ):
        "Run all case"        
#        self.logLog( u"Run all!" )
        self.OnShowRunLog( u"Run all!" )
        for _index in range( len( CaseParser.getCurSelectCaseInfo() ) ):
#            self.test_config_panel.SetCurSelectCaseIndex( _index )
            self.OnChangeTCFGPanelIndex( _index )
#            self.LoadCase()
            self.OnLoad( "event" )
#            self.RunCase()
            self.OnRun( "event" )
            #按照用例方式停止
            self.OnSleepCaseRunTime()
#            time.sleep( CaseParser.getCurRunCaseConfig()['endconfig'][1] )
#            self.EndCase()
            self.OnEnd( "event" )
#            self.OnTimeSleep( 20 )
#            time.sleep( 20 )            
            
#        self.logLog( u"Run all end!" )
        self.OnShowRunLog( u"Run all end!" )
        return True


class MyLog( wx.PyLog ):

    def __init__( self, textCtrl, logTime = 0 ):
        wx.PyLog.__init__( self )
        self.tc = textCtrl
        self.logTime = logTime

    def DoLogString( self, message, timeStamp ):
        if self.tc:
            self.tc.AppendText( message + '\n' )
                      
def MainAUI():

    frame = AuiFrame( None, -1, "Test Platform", style = wx.CAPTION | wx.MAXIMIZE | wx.CLOSE_BOX | wx.RESIZE_BOX | wx.MINIMIZE_BOX | wx.SYSTEM_MENU )
#    frame = AuiFrame( None, -1, "Test Platform", size = ( 800, 600 ) )
    frame.CenterOnScreen()
    frame.Show()
    return frame

#----------------------------------------------------------------------


class testPlantFrame:
    def __init__( self ):
#        frame = wx.Frame(None, -1, "test Platform frame: ", pos = (50, 50), size = (600, 800),
#                        style = wx.DEFAULT_FRAME_STYLE, name = "run a sample")
        self.win = MainAUI()

class MyApp( wx.App ): 
    def OnInit( self ):
        sim = testPlantFrame()
        return 1
            
if __name__ == '__main__':        
    #import sys, os
#    import run
#    run.main(['', os.path.basename(sys.argv[0])] + sys.argv[1:])
    app = MyApp( 0 )
    app.MainLoop()
    
