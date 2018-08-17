# -*- coding: utf-8 -*-
"""
@author: Yusuke Takahashi, Taro Suzuki, Waseda University
"""
import sys,os,shlex,glob,time,re
from subprocess import Popen,PIPE,check_output
from PyQt5.QtWidgets import (QWidget, QPushButton,QHBoxLayout, QVBoxLayout,QCheckBox,QGroupBox,QScrollArea,
 QApplication,QSizePolicy,QMainWindow,QMessageBox,QDialog,QTabWidget,QComboBox,QLabel,QLineEdit,QFormLayout,QGridLayout)
from PyQt5.QtGui import QFont,QColor,QPixmap
from PyQt5 import QtCore
import telnetlib

# Main Window
class MainWindow(QMainWindow):
    dirtrs = os.path.dirname(os.path.abspath(__file__))
    dirrtk = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

    # ublox command file for Base mode
    ubxcmd = dirtrs+'/conf/ubx_m8t_bds_raw_1hz.cmd'

    # Default Base position configuration
    basepos_type=(['LLH','RTCM'])
    basepos_itype=0
    basepos_lat='35.0'
    basepos_lon='139.0'
    basepos_hgt='50.0'

    # Default Input stream configration
    input_port = (['serial0','serial1','ttyACM0','ttyACM1','ttyUSB0','ttyUSB1'])
    input_bitrate = (['300','600','1200','2400','4800','9600','19200','38400','57600','115200','230400'])
    input_bytesize = (['7 bits','8 bits'])   #[7 8]
    input_parity = (['None','Even','Odd'])   #[n e o]
    input_stopbits = (['1 bit','2 bits'])    #[1 2]
    input_flowcontrol = (['None','RTS/CTS']) #[off rtscts]
    input_iport=2
    input_ibitrate = 9
    input_ibytesize = 1
    input_iparity = 0
    input_istopbits = 0
    input_iflowcontrol = 0

    # Default Correction stream configration
    corr_flag = False
    corr_type=(['NTRIP Client','TCP Client'])
    corr_itype=0
    corr_format=(['RTCM2','RTCM3','BINEX','UBX'])
    corr_iformat=1
    corr_user = 'user'
    corr_addr = 'test.net'
    corr_port = '2101'
    corr_pw = 'password'
    corr_mp = 'RTCM'

    # Default Log/Solution stream configration
    log_flag = True
    sol_flag = True
    dir = glob.glob('/media/*/*/')
    if len(dir)==0:
        dir = [dirtrs+'/']
    sol_filename = dir[0]+'%Y-%m%d-%h%M%S.pos'
    log_filename = dir[0]+'%Y-%m%d-%h%M%S.ubx'

    # Default Output stream configration
    output_flag = False
    output_type=(['TCP Server','NTRIP Server','NTRIP Caster'])
    output_itype=1
    output_format=(['UBX','RTCM3'])
    output_iformat=0
    output_user = 'user'
    output_addr = 'test.net'
    output_port = '2101'
    output_pw = 'password'
    output_mp = 'TRS'

    # Default Output(Serial) stream configration
    output2_flag = False
    output2_port = (['serial0','serial1','ttyACM0','ttyACM1','ttyUSB0','ttyUSB1'])
    output2_bitrate = (['300','600','1200','2400','4800','9600','19200','38400','57600','115200','230400'])
    output2_bytesize = (['7 bits','8 bits'])   #[7 8]
    output2_parity = (['None','Even','Odd'])   #[n e o]
    output2_stopbits = (['1 bit','2 bits'])    #[1 2]
    output2_flowcontrol = (['None','RTS/CTS']) #[off rtscts]
    output2_iport=4
    output2_ibitrate = 9
    output2_ibytesize = 1
    output2_iparity = 0
    output2_istopbits = 0
    output2_iflowcontrol = 0

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.rover_timer = QtCore.QTimer(self)
        self.rover_timer.timeout.connect(self.updateRover)
        self.base_timer = QtCore.QTimer(self)
        self.base_timer.timeout.connect(self.updateBase)
        self.main_w = MainWidget()
        self.setCentralWidget(self.main_w)

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        #self.setGeometry(100, 100, 480, 320)
        self.showFullScreen()

        self.show()

    def updateRover(self):
        rawsol=self.main_w.rtkrcvCommand(self.main_w.tn,'solution')
        print(rawsol)
        if len(rawsol)>34:
            soltypes=re.findall(r'\(.*\)',rawsol)
            soltype=soltypes[0][1:-1].strip()
            sols=re.findall(r'\d*\.\d*',rawsol)

            self.main_w.lSol.setText(soltype)
            if soltype=='SINGLE':
                self.main_w.lSol.setStyleSheet('color: #ff0000; font-family: Helvetica; font-size: 11pt')
            if soltype=='FLOAT':
                self.main_w.lSol.setStyleSheet('color: #ffd700; font-family: Helvetica; font-size: 11pt')
            if soltype=='FIX':
                self.main_w.lSol.setStyleSheet('color: #008000; font-family: Helvetica; font-size: 11pt')
            self.main_w.lLat.setText(sols[1])
            self.main_w.lLon.setText(sols[2])
            self.main_w.lAlt.setText(sols[3])

        rawstream=self.main_w.rtkrcvCommand(self.main_w.tn,'stream')
        rawstreams=rawstream.split('\n')

        statstr=''
        for stream in rawstreams:
            if stream.find('error')>0:
                streams=stream.split()
                statstr=streams[0]+' stream error'
            if stream.find(' C ')>0:
                streams=stream.split()
                if streams[0]=='input':
                    statstr=statstr+streams[1]+':'+streams[6]+'bps  '
                else:
                    statstr=statstr+streams[0]+':'+streams[8]+'bps  '
        self.main_w.status_rov.setText(statstr)

    def updateBase(self):
        rawstream = self.p.stderr.readline().decode('utf-8')
        print(rawstream)

        if (rawstream=='stream server start error'):
            self.main_w.status_base.setText('stream server start error\n')

        streams=rawstream.split()
        if len(streams)==9:
            self.main_w.status_base.setText(streams[0]+' '+streams[1]+' '+streams[5]+'bps '+streams[8])
        if len(streams)>=10:
            self.main_w.status_base.setText(streams[0]+' '+streams[1]+' '+streams[5]+'bps '+streams[8]+' '+streams[10])

# Main Widget Class
class MainWidget(QWidget):

    # telnet port for rtkrcv
    tnport=1234

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setFont(QFont('Helvetica',11))

        fig=QPixmap(MainWindow.dirtrs+'/img/banner.png')
        bannar=QLabel(self)
        bannar.setPixmap(fig)
        self.tabs=QTabWidget()

        self.tabRover=QWidget()
        self.tabBase=QWidget()

        self.tabs.addTab(self.tabRover,'Rover')
        self.tabs.addTab(self.tabBase,'Base')

        self.tabRoverUI()
        self.tabBaseUI()

        vbox=QVBoxLayout()
        vbox.addWidget(bannar)
        vbox.addWidget(self.tabs)
        self.setLayout(vbox)

    def tabRoverUI(self):
        # Start button
        self.start_rov = QPushButton('Start',self)
        self.start_rov.setCheckable(True)
        self.start_rov.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.start_rov.toggled.connect(self.startRoverToggled)
        self.start_rov.setFont(QFont('Helvetica',16))
        # Config button
        self.config_rov = QPushButton('Config',self)
        self.config_rov.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.config_rov.clicked.connect(self.makeRoverConfig)
        self.config_rov.setFont(QFont('Helvetica',16))
        # Command window
        self.status_rov = QLabel('')
        self.status_rov.setFont(QFont('Helvetica',11))
        scroll=QScrollArea()
        scroll.setFrameShape(False)
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(25)
        scroll.setWidget(self.status_rov)
        # Icon
        fig=QPixmap(MainWindow.dirtrs+'/img/rover.png')
        icon=QLabel(self)
        icon.setPixmap(fig)
        # Layout
        hbox1 = QHBoxLayout()
        hbox2 = QHBoxLayout()
        hbox3 = QHBoxLayout()
        vbox1_1 = QVBoxLayout()
        hbox1_1 = QHBoxLayout()
        hbox1_2 = QHBoxLayout()
        hbox1_3 = QHBoxLayout()
        vbox = QVBoxLayout()
        # hbox1
        hbox1.addSpacing(10)
        hbox1.addWidget(icon)
        hbox1.addSpacing(10)

        self.mode_spp = QPushButton('Single',self)
        self.mode_spp.setCheckable(True)
        self.mode_spp.toggle()
        self.mode_spp.toggled.connect(self.sppToggled)
        self.mode_spp.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.mode_rtks = QPushButton('RTK\n(Static)',self)
        self.mode_rtks.setCheckable(True)
        self.mode_rtks.toggled.connect(self.rtksToggled)
        self.mode_rtks.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.mode_rtkk = QPushButton('RTK\n(Kinematic)',self)
        self.mode_rtkk.setCheckable(True)
        self.mode_rtkk.toggled.connect(self.rtkkToggled)
        self.mode_rtkk.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        hbox1_2.addWidget(self.mode_spp)
        hbox1_2.addWidget(self.mode_rtks)
        hbox1_2.addWidget(self.mode_rtkk)

        vbox1_1.addLayout(hbox1_2)
        hbox1_3.addWidget(self.start_rov)
        hbox1_3.addWidget(self.config_rov)
        vbox1_1.addLayout(hbox1_3)
        hbox1.addLayout(vbox1_1)

        #
        lSol_=QLabel('Sol:')
        lSol_.setAlignment(QtCore.Qt.AlignRight)
        self.lSol=QLabel('')
        lLat_=QLabel('Lat:')
        lLat_.setAlignment(QtCore.Qt.AlignRight)
        self.lLat=QLabel('')
        lLon_=QLabel('Lon:')
        lLon_.setAlignment(QtCore.Qt.AlignRight)
        self.lLon=QLabel('')
        lAlt_=QLabel('Alt:')
        lAlt_.setAlignment(QtCore.Qt.AlignRight)
        self.lAlt=QLabel('')
        hbox2.addWidget(lSol_)
        hbox2.addWidget(self.lSol)
        hbox2.addWidget(lLat_)
        hbox2.addWidget(self.lLat)
        hbox2.addWidget(lLon_)
        hbox2.addWidget(self.lLon)
        hbox2.addWidget(lAlt_)
        hbox2.addWidget(self.lAlt)

        # hbox3
        hbox3.addWidget(scroll)
        # Add to layout
        vbox.addLayout(hbox1,1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)
        # Show layout
        self.tabRover.setLayout(vbox)

    def makeRoverConfig(self):
        pass
        subWindow=RoverConfigWindow(self)
        subWindow.show()

    def tabBaseUI(self):
        # Start button
        self.start_base = QPushButton('Start',self)
        self.start_base.setCheckable(True)
        self.start_base.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.start_base.toggled.connect(self.startBaseToggled)
        self.start_base.setFont(QFont('Helvetica',16))
        # Config button
        self.config_base = QPushButton('Config',self)
        self.config_base.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.config_base.clicked.connect(self.makeBaseConfig)
        self.config_base.setFont(QFont('Helvetica',16))
        # Command window
        self.status_base = QLabel('')
        self.status_base.setFont(QFont('Helvetica',11))
        scroll=QScrollArea()
        scroll.setFrameShape(False)
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(25)
        scroll.setWidget(self.status_base)
        # Icon
        fig=QPixmap(MainWindow.dirtrs+'/img/base.png')
        icon=QLabel(self)
        icon.setPixmap(fig)
        # Layout
        hbox1 = QHBoxLayout()
        hbox2 = QHBoxLayout()
        vbox = QVBoxLayout()
        # hbox1
        hbox1.addSpacing(10)
        hbox1.addWidget(icon)
        hbox1.addSpacing(10)
        hbox1.addWidget(self.start_base)
        hbox1.addWidget(self.config_base)
        # hbox2
        hbox2.addWidget(scroll)
        # Add to layout
        vbox.addLayout(hbox1,1)
        vbox.addLayout(hbox2)
        # Show layout
        self.tabBase.setLayout(vbox)

    def makeBaseConfig(self):
        subWindow=BaseConfigWindow(self)
        subWindow.show()

    def rtkrcvCommand(self,tn,cmd):
        sendcmd=cmd+'\r\n'
        tn.write(sendcmd.encode())
        ret=tn.read_until(b'rtkrcv> ')
        return ret.decode()

    def rtkrcvOption(self,tn,opt,val):
        cmd='set '+opt+' '+val
        self.rtkrcvCommand(tn,cmd)

    def rtkrcvSetStream(self,tn,name,stype,sformat,spath):
        self.rtkrcvOption(tn,name+'-type',stype)
        self.rtkrcvOption(tn,name+'-format',sformat)
        self.rtkrcvOption(tn,name+'-path',spath)

    # Start Rover button
    def startRoverToggled(self,checked):
        if checked:
            self.start_rov.setText('Stop')
            self.mode_spp.setDisabled(True)
            self.mode_rtks.setDisabled(True)
            self.mode_rtkk.setDisabled(True)
            self.config_rov.setDisabled(True)
            self.tabs.setTabEnabled(1, False)
            exe = MainWindow.dirrtk+'/RTKLIB/app/rtkrcv/gcc/rtkrcv'

            optfile='single.conf'
            if self.mode_rtks.isChecked():
                optfile='static.conf'
            if self.mode_rtkk.isChecked():
                optfile='kinematic.conf'

            main.p = Popen(exe+' -o '+MainWindow.dirtrs+'/conf/'+optfile+' -p '+str(self.tnport)+' -m 52001', shell=True)
            time.sleep(1)
            self.tn = telnetlib.Telnet('localhost',self.tnport)

            # login
            self.tn.read_until(b'password: ')
            self.rtkrcvCommand(self.tn,'admin')

            # Stream setting
            itype,iformat,ipath,otype,oformat,opath,ltype,lformat,lpath = self.makeCommandRover()
            for i,path in enumerate(ipath):
                self.rtkrcvSetStream(self.tn,'inpstr'+str(i+1),itype[i],iformat[i],path)
            for i,path in enumerate(opath):
                self.rtkrcvSetStream(self.tn,'outstr'+str(i+1),otype[i],oformat[i],path)
            for i,path in enumerate(lpath):
                self.rtkrcvSetStream(self.tn,'logstr'+str(i+1),ltype[i],lformat[i],path)

            # Base position
            basepos=(['llh','rtcm'])
            self.rtkrcvOption(self.tn,'ant2-postype',basepos[MainWindow.basepos_itype])
            self.rtkrcvOption(self.tn,'ant2-pos1',MainWindow.basepos_lat)
            self.rtkrcvOption(self.tn,'ant2-pos2',MainWindow.basepos_lon)
            self.rtkrcvOption(self.tn,'ant2-pos3',MainWindow.basepos_hgt)

            self.rtkrcvCommand(self.tn,'start')
            main.rover_timer.start(1000)
        else:
            self.start_rov.setText('Start')
            self.mode_spp.setDisabled(False)
            self.mode_rtks.setDisabled(False)
            self.mode_rtkk.setDisabled(False)
            self.config_rov.setDisabled(False)
            self.tabs.setTabEnabled(1, True)

            main.rover_timer.stop()
            main.p.terminate()
            time.sleep(0.2)

            # shutdown
            self.tn.write('shutdown\r\n'.encode())

            self.status_rov.setText('')
            self.lSol.setText('')
            self.lLat.setText('')
            self.lLon.setText('')
            self.lAlt.setText('')

    # Start Base button
    def startBaseToggled(self,checked):
        if checked:
            self.start_base.setText('Stop')
            self.config_base.setDisabled(True)
            self.tabs.setTabEnabled(0, False)
            exe = MainWindow.dirrtk+'/RTKLIB/app/str2str/gcc/str2str'
            rcvcmd =' -c '+MainWindow.ubxcmd
            llhcmd =' -p '+MainWindow.basepos_lat+' '+MainWindow.basepos_lon+' '+MainWindow.basepos_hgt
            rtcmcmd=' -msg 1006(10),1004,1019'
            opt = self.makeCommandBase()
            cmd = shlex.split(exe+opt+rcvcmd+llhcmd+rtcmcmd)
            main.p = Popen(cmd, stdin=PIPE, stderr=PIPE, bufsize=0)
            main.base_timer.start(1000)
        else:
            self.start_base.setText('Start')
            self.config_base.setDisabled(False)
            self.tabs.setTabEnabled(0, True)
            main.p.stderr.close()
            main.base_timer.stop()
            main.p.terminate()
            self.status_base.setText('')

    # Single
    def sppToggled(self,checked):
        if checked:
            self.mode_rtks.setChecked(False)
            self.mode_rtkk.setChecked(False)

    # RTK-Static
    def rtksToggled(self,checked):
        if checked:
            self.mode_spp.setChecked(False)
            self.mode_rtkk.setChecked(False)

    # RTK-Kinematic
    def rtkkToggled(self,checked):
        if checked:
            self.mode_spp.setChecked(False)
            self.mode_rtks.setChecked(False)

    # Generating commands
    def makeCommandRover(self):
        corrtypes=['ntripcli','tcpcli']
        corrformats=['rtcm2','rtcm3','binex','ubx']

        # input
        itype=[]
        iformat=[]
        ipath=[]
        itype.append('serial')
        iformat.append('ubx')
        ipath.append(self.makeInputCmd(1))
        if MainWindow.corr_flag:
            itype.append(corrtypes[MainWindow.corr_itype])
            iformat.append(corrformats[MainWindow.corr_iformat])
            if MainWindow.corr_itype==0: # NTRIP Client
                ipath.append(self.makeNtripCliCmd())
            elif MainWindow.corr_itype==1: # TCP Client
                ipath.append(self.makeTcpCliCmd())

        # output
        otype=[]
        oformat=[]
        opath=[]
        if MainWindow.sol_flag:
            otype.append('file')
            oformat.append('llh')
            opath.append(self.makeSolCmd())

        # log
        ltype=[]
        lformat=[]
        lpath=[]
        if MainWindow.log_flag:
            ltype.append('file')
            lformat.append('')
            lpath.append(self.makeLogCmd(1))
        print(itype)
        print(iformat)
        print(ipath)
        return itype,iformat,ipath,otype,oformat,opath,ltype,lformat,lpath

    def makeCommandBase(self):
        outputformats=['ubx','rtcm3']
        cmd=self.makeInputCmd(2)
        if MainWindow.log_flag:
            cmd=cmd+self.makeLogCmd(2)

        if MainWindow.output_flag:
            if MainWindow.output_itype==0:
                cmd=cmd+self.makeTcpSvrCmd()
            if MainWindow.output_itype==1:
                cmd=cmd+self.makeNtripSvrCmd()
            if MainWindow.output_itype==2:
                cmd=cmd+self.makeNtripCasCmd()
            # Format conversion
            if MainWindow.output_iformat:
                cmd=cmd+'#'+outputformats[MainWindow.output_iformat]

        if MainWindow.output2_flag:
            cmd=cmd+self.makeSerialOutputCmd()
            # Format conversion
            if MainWindow.output_iformat:
                cmd=cmd+'#'+outputformats[MainWindow.output_iformat]
        return cmd

    def makeInputCmd(self,sta):
        byte_s = (['7','8'])
        parity_s = (['n','e','o'])
        stopb_s =(['1','2'])
        flwctr_s =(['off','rtscts'])
        port    =MainWindow.input_port[MainWindow.input_iport]
        bitrate =MainWindow.input_bitrate[MainWindow.input_ibitrate]
        byte = byte_s[MainWindow.input_ibytesize]
        parity = parity_s[MainWindow.input_iparity]
        stopb = stopb_s[MainWindow.input_istopbits]
        flwctr = flwctr_s[MainWindow.input_iflowcontrol]
        cmd = port+':'+bitrate+':'+byte+':'+parity+':'+stopb+':'+flwctr
        if sta==2: # for str2str
            cmd=' -in serial://'+cmd+'#ubx'
        return cmd

    def makeTcpCliCmd(self):
        addr=MainWindow.corr_addr
        port=MainWindow.corr_port
        return addr+':'+port

    def makeNtripCliCmd(self):
        user= MainWindow.corr_user
        pw  = MainWindow.corr_pw
        port= MainWindow.corr_port
        mp  = MainWindow.corr_mp
        addr= MainWindow.corr_addr
        return user+':'+pw+'@'+addr+':'+port+'/'+mp

    def makeSolCmd(self):
        filename=MainWindow.sol_filename
        return filename

    def makeLogCmd(self,sta):
        filename=MainWindow.log_filename
        cmd=filename
        if sta==2: # for str2str
            cmd=' -out file://'+cmd
        return cmd

    def makeTcpSvrCmd(self):
        port=MainWindow.output_port
        return ' -out tcpsvr://:'+port

    def makeNtripSvrCmd(self):
        pw  = MainWindow.output_pw
        port= MainWindow.output_port
        mp  = MainWindow.output_mp
        addr= MainWindow.output_addr
        return ' -out ntrips://:'+pw+'@'+addr+':'+port+'/'+mp

    def makeNtripCasCmd(self):
        user= MainWindow.output_user
        pw  = MainWindow.output_pw
        port= MainWindow.output_port
        mp  = MainWindow.output_mp
        return ' -out ntripc_c://'+user+':'+pw+'@:'+port+'/'+mp

    def makeSerialOutputCmd(self):
        byte_s = (['7','8'])
        parity_s = (['n','e','o'])
        stopb_s =(['1','2'])
        flwctr_s =(['off','rtscts'])
        port    =MainWindow.output2_port[MainWindow.output2_iport]
        bitrate =MainWindow.output2_bitrate[MainWindow.output2_ibitrate]
        byte = byte_s[MainWindow.output2_ibytesize]
        parity = parity_s[MainWindow.output2_iparity]
        stopb = stopb_s[MainWindow.output2_istopbits]
        flwctr = flwctr_s[MainWindow.output2_iflowcontrol]
        return ' -out serial://'+port+':'+bitrate+':'+byte+':'+parity+':'+stopb+':'+flwctr

# Sub window (Rover Config)
class RoverConfigWindow:
    def __init__(self, parent=None):
        self.w = QDialog(parent)
        self.w.setFont(QFont('Helvetica',11))

        self.w.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.w.setGeometry(0, 0, 480, 320)

        self.parent = parent

        tabs = QTabWidget()

        self.tab_input=InputConfig()
        self.tab_corr=CorrectionConfig()
        self.tab_sol=SolConfig()
        self.tab_log=LogConfig()
        self.tab_basepos=BasePosConfig_Rover()
        tabs.addTab(self.tab_input,"Input")
        tabs.addTab(self.tab_corr,"Correction")
        tabs.addTab(self.tab_sol,"Solution")
        tabs.addTab(self.tab_log,"Log")
        tabs.addTab(self.tab_basepos,"BasePos")

        apply_button= QPushButton('Apply')
        apply_button.clicked.connect(self.applyParam)
        close_button= QPushButton('Close')
        close_button.clicked.connect(self.w.close)

        layout = QVBoxLayout()
        layout.addWidget(tabs)

        hbox = QHBoxLayout()
        hbox.addWidget(apply_button,1)
        hbox.addWidget(close_button,1)
        layout.addLayout(hbox)

        self.w.setLayout(layout)

    def applyParam(self):
        MainWindow.input_iport=self.tab_input.port_list.currentIndex()
        MainWindow.input_ibitrate=self.tab_input.bitrate_list.currentIndex()
        MainWindow.input_ibytesize=self.tab_input.bytesize_list.currentIndex()
        MainWindow.input_iparity=self.tab_input.parity_list.currentIndex()
        MainWindow.input_istopbits=self.tab_input.stopbits_list.currentIndex()
        MainWindow.input_iflowcontrol=self.tab_input.flowcontrol_list.currentIndex()

        MainWindow.corr_flag=self.tab_corr.corr_b.isChecked()
        MainWindow.corr_itype=self.tab_corr.type_list.currentIndex()
        MainWindow.corr_iformat=self.tab_corr.format_list.currentIndex()
        MainWindow.corr_addr=self.tab_corr.addr_edit.text()
        MainWindow.corr_port=self.tab_corr.port_edit.text()
        MainWindow.corr_mp=self.tab_corr.mp_edit.text()
        MainWindow.corr_user=self.tab_corr.user_edit.text()
        MainWindow.corr_pw=self.tab_corr.pw_edit.text()

        MainWindow.sol_flag=self.tab_sol.sol_b.isChecked()
        MainWindow.sol_filename=self.tab_sol.output_edit.text()

        MainWindow.log_flag=self.tab_log.log_b.isChecked()
        MainWindow.log_filename=self.tab_log.output_edit.text()

        MainWindow.basepos_itype=self.tab_basepos.type_list.currentIndex()
        MainWindow.basepos_lat=self.tab_basepos.lat_edit.text()
        MainWindow.basepos_lon=self.tab_basepos.lon_edit.text()
        MainWindow.basepos_hgt=self.tab_basepos.hgt_edit.text()

    def show(self):
        self.w.exec_()

# Sub window (Base config)
class BaseConfigWindow:
    def __init__(self, parent=None):
        self.w = QDialog(parent)
        self.w.setFont(QFont('Helvetica',11))

        self.w.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.w.setGeometry(0, 0, 480, 320)

        self.parent = parent

        tabs = QTabWidget()

        self.tab_input=InputConfig()
        self.tab_output1=OutputConfig()
        self.tab_output2=OutputSerialConfig()
        self.tab_log=LogConfig()
        self.tab_basepos=BasePosConfig_Base()
        tabs.addTab(self.tab_input,"Input")
        tabs.addTab(self.tab_output1,"Output1")
        tabs.addTab(self.tab_output2,"Output2")
        tabs.addTab(self.tab_log,"Log")
        tabs.addTab(self.tab_basepos,"BasePos")

        apply_button= QPushButton('Apply')
        apply_button.clicked.connect(self.applyParam)
        close_button= QPushButton('Close')
        close_button.clicked.connect(self.w.close)

        layout = QVBoxLayout()
        layout.addWidget(tabs)

        hbox = QHBoxLayout()
        hbox.addWidget(apply_button,1)
        hbox.addWidget(close_button,1)
        layout.addLayout(hbox)

        self.w.setLayout(layout)

    def applyParam(self):
        MainWindow.input_iport=self.tab_input.port_list.currentIndex()
        MainWindow.input_ibitrate=self.tab_input.bitrate_list.currentIndex()
        MainWindow.input_ibytesize=self.tab_input.bytesize_list.currentIndex()
        MainWindow.input_iparity=self.tab_input.parity_list.currentIndex()
        MainWindow.input_istopbits=self.tab_input.stopbits_list.currentIndex()
        MainWindow.input_iflowcontrol=self.tab_input.flowcontrol_list.currentIndex()

        MainWindow.output_flag=self.tab_output1.output_b.isChecked()
        MainWindow.output_itype=self.tab_output1.type_list.currentIndex()
        MainWindow.output_iformat=self.tab_output1.format_list.currentIndex()
        if self.tab_output1.addr_edit.isEnabled():
        	MainWindow.output_addr=self.tab_output1.addr_edit.text()
        MainWindow.output_port=self.tab_output1.port_edit.text()
        MainWindow.output_mp=self.tab_output1.mp_edit.text()
        MainWindow.output_user=self.tab_output1.user_edit.text()
        MainWindow.output_pw=self.tab_output1.pw_edit.text()

        MainWindow.output2_flag=self.tab_output2.output2_b.isChecked()
        MainWindow.output2_iport=self.tab_output2.port_list.currentIndex()
        MainWindow.output2_ibitrate=self.tab_output2.bitrate_list.currentIndex()
        MainWindow.output2_ibytesize=self.tab_output2.bytesize_list.currentIndex()
        MainWindow.output2_iparity=self.tab_output2.parity_list.currentIndex()
        MainWindow.output2_istopbits=self.tab_output2.stopbits_list.currentIndex()
        MainWindow.output2_iflowcontrol=self.tab_output2.flowcontrol_list.currentIndex()

        MainWindow.log_flag=self.tab_log.log_b.isChecked()
        MainWindow.log_filename=self.tab_log.output_edit.text()

        MainWindow.basepos_lat=self.tab_basepos.lat_edit.text()
        MainWindow.basepos_lon=self.tab_basepos.lon_edit.text()
        MainWindow.basepos_hgt=self.tab_basepos.hgt_edit.text()

    def show(self):
        self.w.exec_()

# Input config
class InputConfig(QWidget):
    def __init__(self,parent=None):
        super().__init__()
        self.initInputUI()

    def initInputUI(self):
        self.port_list=QComboBox(self)
        self.port_list.addItems(MainWindow.input_port)
        self.port_list.setCurrentIndex(MainWindow.input_iport)

        self.bitrate_list=QComboBox(self)
        self.bitrate_list.addItems(MainWindow.input_bitrate)
        self.bitrate_list.setCurrentIndex(MainWindow.input_ibitrate)

        self.bytesize_list=QComboBox(self)
        self.bytesize_list.addItems(MainWindow.input_bytesize)
        self.bytesize_list.setCurrentIndex(MainWindow.input_ibytesize)

        self.parity_list=QComboBox(self)
        self.parity_list.addItems(MainWindow.input_parity)
        self.parity_list.setCurrentIndex(MainWindow.input_iparity)

        self.stopbits_list=QComboBox(self)
        self.stopbits_list.addItems(MainWindow.input_stopbits)
        self.stopbits_list.setCurrentIndex(MainWindow.input_istopbits)

        self.flowcontrol_list=QComboBox(self)
        self.flowcontrol_list.addItems(MainWindow.input_flowcontrol)
        self.flowcontrol_list.setCurrentIndex(MainWindow.input_iflowcontrol)

        #add
        grid=QGridLayout()
        grid.addWidget(QLabel('Port'),0,0)
        grid.addWidget(self.port_list,0,1)
        grid.addWidget(QLabel('Bit Rate'),0,2)
        grid.addWidget(self.bitrate_list,0,3)
        grid.addWidget(QLabel('Byte Size'),1,0)
        grid.addWidget(self.bytesize_list,1,1)
        grid.addWidget(QLabel('Parity'),1,2)
        grid.addWidget(self.parity_list,1,3)
        grid.addWidget(QLabel('Stop Bits'),2,0)
        grid.addWidget(self.stopbits_list,2,1)
        grid.addWidget(QLabel('Flow Control'),2,2)
        grid.addWidget(self.flowcontrol_list,2,3)
        self.setLayout(grid)

# Correction config
class CorrectionConfig(QWidget):
    def __init__(self,parent=None):
        super().__init__()
        self.initCorrectionUI()

    def initCorrectionUI(self):
        self.corr_b = QCheckBox("Enable",self)
        self.type_list=QComboBox(self)
        self.type_list.addItems(MainWindow.corr_type)
        self.type_list.setCurrentIndex(MainWindow.corr_itype)
        self.type_list.currentIndexChanged.connect(self.typeChanged)
        self.format_list=QComboBox(self)
        self.format_list.addItems(MainWindow.corr_format)
        self.format_list.setCurrentIndex(MainWindow.corr_iformat)

        self.corr_b.setChecked(MainWindow.corr_flag)
        self.addr_edit=QLineEdit(MainWindow.corr_addr,self)
        self.port_edit=QLineEdit(MainWindow.corr_port,self)
        self.mp_edit=QLineEdit(MainWindow.corr_mp,self)
        self.user_edit=QLineEdit(MainWindow.corr_user,self)
        self.pw_edit=QLineEdit(MainWindow.corr_pw,self)

        grid=QGridLayout()
        grid.addWidget(self.corr_b,0,0)
        grid.addWidget(QLabel('Type/Format'),0,1)
        grid.addWidget(self.type_list,0,2)
        grid.addWidget(self.format_list,0,3)
        grid.addWidget(QLabel('Address'),1,0)
        grid.addWidget(self.addr_edit,1,1,1,4)
        grid.addWidget(QLabel('Port'),2,0)
        grid.addWidget(self.port_edit,2,1)
        grid.addWidget(QLabel('Mountpoint'),2,2)
        grid.addWidget(self.mp_edit,2,3)
        grid.addWidget(QLabel('User-ID'),3,0)
        grid.addWidget(self.user_edit,3,1)
        grid.addWidget(QLabel('Password'),3,2)
        grid.addWidget(self.pw_edit,3,3)
        self.setLayout(grid)

        self.typeChanged(MainWindow.corr_itype)

    def typeChanged(self,ind):
        if ind==0: # TCP Client
            self.mp_edit.setDisabled(False)
            self.user_edit.setDisabled(False)
            self.pw_edit.setDisabled(False)
        elif ind==1: # NTRIP Client
            self.mp_edit.setDisabled(True)
            self.user_edit.setDisabled(True)
            self.pw_edit.setDisabled(True)

# Output config
class OutputConfig(QWidget):
    def __init__(self,parent=None):
        super().__init__()
        self.initOutputUI()

    def initOutputUI(self):
        self.output_b = QCheckBox("Enable",self)
        self.type_list=QComboBox(self)
        self.type_list.addItems(MainWindow.output_type)
        self.type_list.setCurrentIndex(MainWindow.output_itype)
        self.type_list.currentIndexChanged.connect(self.typeChanged)
        self.format_list=QComboBox(self)
        self.format_list.addItems(MainWindow.output_format)
        self.format_list.setCurrentIndex(MainWindow.output_iformat)

        self.output_b.setChecked(MainWindow.output_flag)
        self.addr_edit=QLineEdit(MainWindow.output_addr,self)
        self.port_edit=QLineEdit(MainWindow.output_port,self)
        self.mp_edit=QLineEdit(MainWindow.output_mp,self)
        self.user_edit=QLineEdit(MainWindow.output_user,self)
        self.pw_edit=QLineEdit(MainWindow.output_pw,self)

        grid=QGridLayout()
        grid.addWidget(self.output_b,0,0)
        grid.addWidget(QLabel('Type/Format'),0,1)
        grid.addWidget(self.type_list,0,2)
        grid.addWidget(self.format_list,0,3)
        grid.addWidget(QLabel('Address'),1,0)
        grid.addWidget(self.addr_edit,1,1,1,4)
        grid.addWidget(QLabel('Port'),2,0)
        grid.addWidget(self.port_edit,2,1)
        grid.addWidget(QLabel('Mountpoint'),2,2)
        grid.addWidget(self.mp_edit,2,3)
        grid.addWidget(QLabel('User-ID'),3,0)
        grid.addWidget(self.user_edit,3,1)
        grid.addWidget(QLabel('Password'),3,2)
        grid.addWidget(self.pw_edit,3,3)
        self.setLayout(grid)
        self.typeChanged(MainWindow.output_itype)

    def typeChanged(self,ind):
        if ind==0: # TCP Server
            self.addr_edit.setText(self.getipadress())
            self.addr_edit.setDisabled(True)
            self.mp_edit.setDisabled(True)
            self.user_edit.setDisabled(True)
            self.pw_edit.setDisabled(True)
        if ind==1: # NTRIP Server
            self.addr_edit.setText(MainWindow.output_addr)
            self.addr_edit.setDisabled(False)
            self.mp_edit.setDisabled(False)
            self.user_edit.setDisabled(True)
            self.pw_edit.setDisabled(False)
        if ind==2: # NTRIP Caster
            self.addr_edit.setText(self.getipadress())
            self.addr_edit.setDisabled(True)
            self.mp_edit.setDisabled(False)
            self.user_edit.setDisabled(False)
            self.pw_edit.setDisabled(False)
        if ind==3: # Serial
            self.addr_edit.setText(self.getipadress())
            self.addr_edit.setDisabled(True)
            self.mp_edit.setDisabled(False)
            self.user_edit.setDisabled(False)
            self.pw_edit.setDisabled(False)

    def getipadress(self):
        host=check_output(['hostname', '-I'])
        hosts=host.split()
        if len(hosts)==0:
            return '127.0.0.1'
        else:
            return hosts[0].decode()

# Output(Serial) config
class OutputSerialConfig(QWidget):
    def __init__(self,parent=None):
        super().__init__()
        self.initOutputSerialUI()

    def initOutputSerialUI(self):
        self.output2_b = QCheckBox("Enable",self)
        self.output2_b.setChecked(MainWindow.output2_flag)

        self.port_list=QComboBox(self)
        self.port_list.addItems(MainWindow.output2_port)
        self.port_list.setCurrentIndex(MainWindow.output2_iport)

        self.bitrate_list=QComboBox(self)
        self.bitrate_list.addItems(MainWindow.output2_bitrate)
        self.bitrate_list.setCurrentIndex(MainWindow.output2_ibitrate)

        self.bytesize_list=QComboBox(self)
        self.bytesize_list.addItems(MainWindow.output2_bytesize)
        self.bytesize_list.setCurrentIndex(MainWindow.output2_ibytesize)

        self.parity_list=QComboBox(self)
        self.parity_list.addItems(MainWindow.output2_parity)
        self.parity_list.setCurrentIndex(MainWindow.output2_iparity)

        self.stopbits_list=QComboBox(self)
        self.stopbits_list.addItems(MainWindow.output2_stopbits)
        self.stopbits_list.setCurrentIndex(MainWindow.output2_istopbits)

        self.flowcontrol_list=QComboBox(self)
        self.flowcontrol_list.addItems(MainWindow.output2_flowcontrol)
        self.flowcontrol_list.setCurrentIndex(MainWindow.output2_iflowcontrol)

        #add
        grid=QGridLayout()
        grid.addWidget(self.output2_b,0,0)
        grid.addWidget(QLabel('Port'),1,0)
        grid.addWidget(self.port_list,1,1)
        grid.addWidget(QLabel('Bit Rate'),1,2)
        grid.addWidget(self.bitrate_list,1,3)
        grid.addWidget(QLabel('Byte Size'),2,0)
        grid.addWidget(self.bytesize_list,2,1)
        grid.addWidget(QLabel('Parity'),2,2)
        grid.addWidget(self.parity_list,2,3)
        grid.addWidget(QLabel('Stop Bits'),3,0)
        grid.addWidget(self.stopbits_list,3,1)
        grid.addWidget(QLabel('Flow Control'),3,2)
        grid.addWidget(self.flowcontrol_list,3,3)
        self.setLayout(grid)

# Solution config
class SolConfig(QWidget):
    def __init__(self,parent=None):
        super().__init__()
        self.initSolUI()

    def initSolUI(self):
        self.sol_b = QCheckBox("Enable",self)
        self.sol_b.setChecked(MainWindow.sol_flag)
        self.output_edit=QLineEdit(MainWindow.sol_filename)

        grid=QGridLayout()
        grid.addWidget(self.sol_b,0,0)
        grid.addWidget(QLabel('Output File name'),1,0)
        grid.addWidget(self.output_edit,1,1)
        self.setLayout(grid)

# Log config
class LogConfig(QWidget):
    def __init__(self,parent=None):
        super().__init__()
        self.initLogUI()

    def initLogUI(self):
        self.log_b = QCheckBox("Enable",self)
        self.log_b.setChecked(MainWindow.log_flag)
        self.output_edit=QLineEdit(MainWindow.log_filename)

        grid=QGridLayout()
        grid.addWidget(self.log_b,0,0)
        grid.addWidget(QLabel('Output File name'),1,0)
        grid.addWidget(self.output_edit,1,1)
        self.setLayout(grid)

# BasePos config
class BasePosConfig_Rover(QWidget):
    def __init__(self,parent=None):
        super().__init__()
        self.initBasePosUI()

    def initBasePosUI(self):
        self.type_list=QComboBox(self)
        self.type_list.addItems(MainWindow.basepos_type)
        self.type_list.setCurrentIndex(MainWindow.basepos_itype)
        self.type_list.currentIndexChanged.connect(self.typeChanged)

        self.lat_edit=QLineEdit(MainWindow.basepos_lat)
        self.lon_edit=QLineEdit(MainWindow.basepos_lon)
        self.hgt_edit=QLineEdit(MainWindow.basepos_hgt)

        grid=QGridLayout()
        grid.addWidget(QLabel('Base Position Type'),0,0)
        grid.addWidget(self.type_list,0,1)
        grid.addWidget(QLabel('Latitude (deg)'),1,0)
        grid.addWidget(self.lat_edit,1,1)
        grid.addWidget(QLabel('Longitude (deg)'),2,0)
        grid.addWidget(self.lon_edit,2,1)
        grid.addWidget(QLabel('Height (m)'),3,0)
        grid.addWidget(self.hgt_edit,3,1)
        self.setLayout(grid)

        self.typeChanged(MainWindow.basepos_itype)

    def typeChanged(self,ind):
        if ind==0: # LLH
            self.lat_edit.setDisabled(False)
            self.lon_edit.setDisabled(False)
            self.hgt_edit.setDisabled(False)
        elif ind==1: # RTCM
            self.lat_edit.setDisabled(True)
            self.lon_edit.setDisabled(True)
            self.hgt_edit.setDisabled(True)

# BasePos config
class BasePosConfig_Base(QWidget):
    def __init__(self,parent=None):
        super().__init__()
        self.initBasePosUI()

    def initBasePosUI(self):
        self.lat_edit=QLineEdit(MainWindow.basepos_lat)
        self.lon_edit=QLineEdit(MainWindow.basepos_lon)
        self.hgt_edit=QLineEdit(MainWindow.basepos_hgt)

        grid=QGridLayout()
        grid.addWidget(QLabel('Latitude (deg)'),0,0)
        grid.addWidget(self.lat_edit,0,1)
        grid.addWidget(QLabel('Longitude (deg)'),1,0)
        grid.addWidget(self.lon_edit,1,1)
        grid.addWidget(QLabel('Height (m)'),2,0)
        grid.addWidget(self.hgt_edit,2,1)
        self.setLayout(grid)

# main
if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = MainWindow()
    sys.exit(app.exec_())
