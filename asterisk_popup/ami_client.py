"""
AMI Client for FreePBX Popup - Asterisk Manager Interface client module.
Handles connection to Asterisk PBX, processes events, and manages call notifications.
"""

import socket
import threading
import time
import logging
from datetime import datetime
from queue import Queue, Empty

logger = logging.getLogger('FreePBXPopup.AMIClient')

class AMIClient:
    """Client for connecting to Asterisk Manager Interface using direct socket connection"""

    def __init__(self, config, notification_callback=None, call_status_callback=None):
        """
        Initialize AMI client

        Args:
            config (ConfigManager): Configuration manager instance
            notification_callback (callable): Callback function for incoming call notifications
            call_status_callback (callable): Callback function for call status changes
        """
        self.config = config
        self.notification_callback = notification_callback
        self.call_status_callback = call_status_callback
        self.socket = None
        self.connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 5
        self._stop_event = threading.Event()
        self._reader_thread = None
        self._event_queue = Queue()
        self._event_thread = None

        self.active_calls = {}

    def start(self):
        """Start the AMI client and connect to the server"""
        logger.info("Starting AMI client")
        self._connect()

        self._event_thread = threading.Thread(target=self._process_events, daemon=True)
        self._event_thread.start()

        while not self._stop_event.is_set():
            if not self.connected and self.reconnect_attempts < self.max_reconnect_attempts:
                logger.info(f"Attempting to reconnect (attempt {self.reconnect_attempts + 1})")
                self._connect()
                self.reconnect_attempts += 1
            time.sleep(self.reconnect_delay)

    def stop(self):
        """Stop the AMI client and disconnect from the server"""
        logger.info("Stopping AMI client")
        self._stop_event.set()
        try:
            if self.socket and self.connected:
                self._send_action({
                    'Action': 'Logoff'
                })
                self.socket.close()
                self.connected = False
                logger.info("AMI client disconnected")
        except Exception as e:
            logger.error(f"Error stopping AMI client: {e}")

    def _connect(self):
        """Connect to the AMI server"""
        try:
            ami_settings = self.config.get_ami_settings()
            host = ami_settings.get('host', 'localhost')
            port = int(ami_settings.get('port', 5038))
            username = ami_settings.get('username', 'admin')
            secret = ami_settings.get('secret', '')

            # If no host is configured, don't attempt to connect
            if not host or host == 'localhost' or host == '127.0.0.1':
                if self.reconnect_attempts == 0:
                    logger.warning("No valid host configured. Please configure AMI settings in preferences.")
                # Limit reconnect attempts for localhost connections
                if self.reconnect_attempts >= 3:
                    logger.warning("Maximum reconnect attempts reached for localhost. Waiting for configuration change.")
                    time.sleep(30)  # Wait longer before retrying localhost connections
                    return

            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)

            logger.info(f"Connecting to {host}:{port}")
            self.socket.connect((host, port))

            welcome = self._read_response()
            logger.debug(f"Welcome message: {welcome}")

            login_response = self._send_action({
                'Action': 'Login',
                'Username': username,
                'Secret': secret
            })

            if 'Success' in login_response:
                logger.info("Login successful")
                self.connected = True
                self.reconnect_attempts = 0

                self.socket.settimeout(0.0)

                self._reader_thread = threading.Thread(target=self._read_events, daemon=True)
                self._reader_thread.start()

                logger.info("Successfully connected to AMI server")
            else:
                logger.error(f"Login failed: {login_response}")
                self.socket.close()
                self.connected = False

        except socket.error as e:
            if self.socket:
                self.socket.close()
            self.connected = False

            # Provide more helpful error messages for common connection issues
            if e.errno == 61:  # Connection refused
                logger.error(f"Connection refused to {ami_settings.get('host', 'localhost')}:{ami_settings.get('port', 5038)}. "
                             f"Please check that the Asterisk server is running and AMI is enabled.")
            elif e.errno == 60:  # Operation timed out
                logger.error(f"Connection timed out to {ami_settings.get('host', 'localhost')}:{ami_settings.get('port', 5038)}. "
                             f"Please check your network connection and firewall settings.")
            elif e.errno == 8:  # Hostname not found
                logger.error(f"Hostname not found: {ami_settings.get('host', 'localhost')}. "
                             f"Please check the hostname in your AMI settings.")
            else:
                logger.error(f"Failed to connect to AMI server: {e}")

        except Exception as e:
            if self.socket:
                self.socket.close()
            self.connected = False
            logger.error(f"Failed to connect to AMI server: {e}")

    def _send_action(self, action_dict):
        """Send an action to the AMI server"""
        try:
            action_str = ''
            for key, value in action_dict.items():
                action_str += f"{key}: {value}\r\n"
            action_str += "\r\n"

            self.socket.sendall(action_str.encode('utf-8'))

            return self._read_response()

        except Exception as e:
            logger.error(f"Error sending action: {e}")
            self.connected = False
            return f"Error: {e}"

    def _read_response(self):
        """Read a response from the AMI server"""
        buffer = b''
        try:
            while not buffer.endswith(b'\r\n\r\n') and not buffer.endswith(b'\n\n'):
                chunk = self.socket.recv(4096)
                if not chunk:
                    break
                buffer += chunk

            return buffer.decode('utf-8')
        except socket.timeout:
            logger.error("Socket timeout while reading response")
            return "Error: Socket timeout"
        except Exception as e:
            logger.error(f"Error reading response: {e}")
            return f"Error: {e}"

    def _read_events(self):
        """Read events from the AMI server continuously"""
        buffer = b''

        while not self._stop_event.is_set() and self.connected:
            try:
                try:
                    chunk = self.socket.recv(4096)
                    if not chunk:
                        logger.warning("Connection closed by server")
                        self.connected = False
                        break

                    buffer += chunk
                except socket.error as e:
                    if e.args[0] == socket.EWOULDBLOCK or e.args[0] == socket.EAGAIN:
                        time.sleep(0.1)
                        continue
                    else:
                        logger.error(f"Socket error: {e}")
                        self.connected = False
                        break

                while b'\r\n\r\n' in buffer or b'\n\n' in buffer:
                    end_pos = buffer.find(b'\r\n\r\n')
                    if end_pos == -1:
                        end_pos = buffer.find(b'\n\n')
                        end_len = 2
                    else:
                        end_len = 4

                    event_data = buffer[:end_pos + end_len]
                    buffer = buffer[end_pos + end_len:]

                    event = self._parse_event(event_data.decode('utf-8'))
                    if event:
                        self._event_queue.put(event)

            except Exception as e:
                logger.error(f"Error in event reader: {e}")
                self.connected = False
                break

        logger.info("Event reader thread stopped")

    def _parse_event(self, event_str):
        """Parse an event string into a dictionary"""
        event = {}

        if 'Event:' not in event_str:
            return None

        for line in event_str.split('\r\n'):
            if not line or line.isspace():
                continue

            parts = line.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                event[key] = value

        return event

    def _process_events(self):
        """Process events from the queue"""
        while not self._stop_event.is_set():
            try:
                try:
                    event = self._event_queue.get(timeout=0.5)
                except Empty:
                    continue

                event_type = event.get('Event')
                if event_type == 'FullyBooted':
                    self._handle_fully_booted(event)
                elif event_type == 'Newchannel':
                    self._handle_newchannel(event)
                elif event_type == 'Newstate':
                    self._handle_newstate(event)
                elif event_type == 'NewCallerid':
                    self._handle_newcallerid(event)
                elif event_type == 'Hangup':
                    self._handle_hangup(event)

                self._event_queue.task_done()

            except Exception as e:
                logger.error(f"Error processing event: {e}")

        logger.info("Event processing thread stopped")

    def _handle_fully_booted(self, _):
        """Handle FullyBooted event"""
        logger.info("Asterisk server fully booted")

    def _handle_newchannel(self, event):
        """Handle Newchannel event"""
        logger.debug(f"New channel event: {event}")

        if event.get('Context') == 'from-trunk' and event.get('ChannelStateDesc') == 'Ring':
            logger.info(f"Incoming call detected on channel {event.get('Channel')}")

    def _handle_newstate(self, event):
        """Handle Newstate event"""
        logger.debug(f"New state event: {event}")

        channel = event.get('Channel')
        channel_state = event.get('ChannelStateDesc')

        if (channel_state == 'Ringing' and
            event.get('CallerIDNum') and
            event.get('ConnectedLineNum')):

            extension = event.get('ConnectedLineNum')

            extensions_to_monitor = self.config.get_extensions_to_monitor()
            if not extensions_to_monitor or extension in extensions_to_monitor:
                caller_id_num = event.get('CallerIDNum')
                caller_id_name = event.get('CallerIDName', 'Unknown')

                logger.info(f"Incoming call from {caller_id_name} <{caller_id_num}> to extension {extension}")

                call_info = {
                    'caller_id_num': caller_id_num,
                    'caller_id_name': caller_id_name,
                    'extension': extension,
                    'channel': channel,
                    'timestamp': datetime.now(),
                    'status': 'ringing'
                }
                self.active_calls[channel] = call_info

                if self.notification_callback:
                    self.notification_callback(call_info)

        elif channel_state == 'Up' and channel in self.active_calls:
            self.active_calls[channel]['status'] = 'answered'

            if self.call_status_callback:
                self.call_status_callback(channel, 'answered')

    def _handle_newcallerid(self, event):
        """Handle NewCallerid event"""
        logger.debug(f"New caller ID event: {event}")

    def _handle_hangup(self, event):
        """Handle Hangup event"""
        logger.debug(f"Hangup event: {event}")

        channel = event.get('Channel')

        if channel in self.active_calls:
            call_info = self.active_calls[channel]

            call_info['status'] = 'hangup'
            call_info['hangup_cause'] = event.get('Cause')
            call_info['hangup_cause_text'] = event.get('Cause-txt')

            if self.call_status_callback:
                self.call_status_callback(channel, 'hangup')

            def remove_call():
                if channel in self.active_calls:
                    del self.active_calls[channel]

            threading.Timer(5.0, remove_call).start()

    def is_connected(self):
        """Check if the AMI client is connected"""
        return self.connected

    def get_status(self):
        """Get the current status of the AMI client"""
        return {
            'connected': self.connected,
            'reconnect_attempts': self.reconnect_attempts,
        }

    def get_extensions(self):
        """Get a list of available extensions"""
        if not self.connected or not self.socket:
            return []

        try:
            self._send_action({
                'Action': 'SIPpeers'
            })

            extensions = []
            return extensions
        except Exception as e:
            logger.error(f"Failed to get extensions: {e}")
            return []
