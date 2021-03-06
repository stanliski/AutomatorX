#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import time

import wda
import subprocess32 as subprocess
from PIL import Image
from StringIO import StringIO

from atx.drivers.mixin import DeviceMixin, hook_wrap
from atx.drivers import Display
from atx import consts
from atx import ioskit

__dir__ = os.path.dirname(os.path.abspath(__file__))


class IOSDevice(DeviceMixin):
    def __init__(self, device_url, bundle_id=None):
        DeviceMixin.__init__(self)
        self.__device_url = device_url
        self.__display = None
        self.__scale = None
        
        self._wda = wda.Client(device_url)
        self._session = None
        self._bundle_id = None

        if bundle_id:
            self.start_app(bundle_id)
        # ioskit.Device.__init__(self, udid)

        # # xcodebuild -project  -scheme WebDriverAgentRunner -destination "id=1002c0174e481a651d71e3d9a89bd6f90d253446" test
        # # Test Case '-[UITestingUITests testRunner]' started.
        # xproj_dir = os.getenv('WEBDRIVERAGENT_DIR')
        # if not xproj_dir:
        #     raise RuntimeError("env-var WEBDRIVERAGENT_DIR need to be set")

        # proc = self._xcproc = subprocess.Popen(['/usr/bin/xcodebuild',
        #     '-project', 'WebDriverAgent.xcodeproj',
        #     '-scheme', 'WebDriverAgentRunner',
        #     '-destination', 'id='+self.udid, 'test'],
        #     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=xproj_dir, bufsize=1, universal_newlines=True)
        # for line in iter(proc.stdout.readline, b""):
        #     print 'STDOUT:', line.strip()
        #     if 'TEST FAILED' in line:
        #         raise RuntimeError("webdriver start test failed, maybe need to unlock the keychain, try\n" + 
        #             '$ security unlock-keychain ~/Library/Keychains/login.keychain')
        #     elif "Successfully wrote Manifest cache" in line:
        #         print 'GOOD ^_^, wait 5s'
        #         time.sleep(5.0)
        #         break

    def start_app(self, bundle_id):
        """Start an application
        Args:
            - bundle_id: (string) apk bundle ID

        Returns:
            WDA session object
        """
        # if self._session is not None:
        #     self.stop_app()
        self._bundle_id = bundle_id
        self._session = self._wda.session(bundle_id)
        return self._session

    def stop_app(self, *args):
        if self._session is None:
            return
        self._session.close()
        self._session = None
        self._bundle_id = None

    def __call__(self, *args, **kwargs):
        if self._session is None:
            raise RuntimeError("Need to call start_app before")
        return self._session(*args, **kwargs)

    def status(self):
        """ Check if connection is ok """
        return self._wda.status()

    @property
    def display(self):
        """ Get screen width and height """
        if not self.__display:
            self.screenshot()
        return self.__display

    @property
    def bundle_id(self):
        return self._bundle_id

    @property
    def scale(self):
        if self.__scale:
            return self.__scale
        if self._session is None:
            raise RuntimeError("Need to call start_app before")
        wsize = self._session.window_size()
        self.__scale = min(self.display) / min(wsize)
        return self.__scale
    
    @property
    def rotation(self):
        """Rotation of device
        Returns:
            int (0-3)
        """
        rs = dict(PORTRAIT=0, LANDSCAPE=1, UIA_DEVICE_ORIENTATION_LANDSCAPERIGHT=3)
        return rs.get(self._session.orientation, 0)

    def click(self, x, y):
        """Simulate click operation
        Args:
            x, y(int): position
        """
        if self._session is None:
            raise RuntimeError("Need to call start_app before")
        if not self.__scale:
            raw_size = self._session.window_size()
            self.__scale = min(self.display) / min(raw_size)
        rx, ry = x/self.__scale, y/self.__scale
        self._session.tap(rx, ry)
        return self

    def home(self):
        """ Return to homescreen """
        return self._wda.home()

    @hook_wrap(consts.EVENT_SCREENSHOT)
    def screenshot(self, filename=None):
        """Take a screenshot
        Args:
            - filename(string): file name to save

        Returns:
            PIL Image object
        """
        raw_png = self._wda.screenshot()
        img = Image.open(StringIO(raw_png))
        if filename:
            img.save(filename)
        if not self.__display:
            self.__display = Display(*sorted(img.size))
        return img
