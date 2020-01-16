from twisted.internet import reactor, defer
from quarry.net.proxy import DownstreamFactory, Bridge

from quarry.net.auth import Profile


import packet_manager
import importlib
import time


HELP_MSG = """§a!/phelp                Show this message
§a!/save                 Save all previouse chat and tab packets to file
§a!/playback <filename>  Playback packest from file
§a!/rl                   Reload and terminate packet playback
§a!/quiet                Mute/Unmute chat"""

print("Log into mojang:")
EMAIL, PASSWORD = input("email > "), input("Password > ")
print("Waiting for connection...")


class QuietBridge(Bridge):
    quiet_mode = False
    count = 0
    packets = []

    def packet_upstream_chat_message(self, buff):
        client_command = False
        buff.save()
        chat_message = self.read_chat(buff, "upstream")

        if chat_message.startswith("/help"):
            self.downstream.send_packet("chat_message", self.write_chat("§a!Do /phelp for proxy commands help", "downstream"))
            buff.restore()
            self.upstream.send_packet("chat_message", buff.read())

        elif chat_message.startswith("/phelp"):
            self.downstream.send_packet("chat_message", self.write_chat(HELP_MSG, "downstream"))

        elif chat_message.startswith("/save"):
            fname = "packet_log-%s.txt"%(str(time.time()).split(".")[0])
            with open(fname, "a") as f:
                while len(self.packets) != 0:
                    l = self.packets.pop(0)

                    f.write("%s || %s || %s\n"%l)

            self.downstream.send_packet("chat_message", self.write_chat("§a!Saved data to: %s"%fname, "downstream"))


        elif chat_message.startswith("/playback"):
            try:
                a = packet_manager.read_file(self, chat_message.split(" ", 1)[1])
                self.downstream.send_packet("chat_message", self.write_chat(a, "downstream"))
            except IndexError:
                self.downstream.send_packet("chat_message", self.write_chat("§c!No file provided.", "downstream"))

        elif chat_message.startswith("/rl"):
            packet_manager.reload()
            importlib.reload(packet_manager)
            self.downstream.send_packet("chat_message", self.write_chat("§a!Reloaded module", "downstream"))


        elif chat_message.startswith("/quiet"):
            client_command = True
            # Switch mode
            self.quiet_mode = not self.quiet_mode

            action = self.quiet_mode and "enabled" or "disabled"
            msg = "§a!Quiet mode %s" % action
            self.downstream.send_packet("chat_message", self.write_chat(msg, "downstream"))

        elif self.quiet_mode and not client_command:
            # Don't let the player send chat messages in quiet mode
            msg = "§c!Can't send messages while in quiet mode"
            self.downstream.send_packet("chat_message", self.write_chat(msg, "downstream"))

        else:
            # Pass to upstream
            buff.restore()
            self.upstream.send_packet("chat_message", buff.read())

    def packet_downstream_chat_message(self, buff):

        self.count += 1


        packet_manager.handle(self, buff, "downstream", "chat_message")


        chat_message = self.read_chat(buff, "downstream")
        if self.quiet_mode and not chat_message.startswith("!"):
            # Ignore message we're in quiet mode and it looks like chat
            pass

        else:
            # Pass to downstream
            buff.restore()
            self.downstream.send_packet("chat_message", buff.read())


    def read_chat(self, buff, direction):
        buff.save()
        if direction == "upstream":
            p_text = buff.unpack_string()
            return p_text
        elif direction == "downstream":
            p_text = str(buff.unpack_chat())

            # 1.7.x
            if self.upstream.protocol_version <= 5:
                p_position = 0

            # 1.8.x
            else:
                p_position = buff.unpack('B')

            if p_position in (0, 1):
                return p_text

    def write_chat(self, text, direction):
        if direction == "upstream":
            return self.buff_type.pack_string(text)
        elif direction == "downstream":
            data = self.buff_type.pack_chat(text)

            # 1.7.x
            if self.downstream.protocol_version <= 5:
                pass

            # 1.8.x
            else:
                data += self.buff_type.pack('B', 0)

            return data


    def packet_unhandled(self, buff, direction, name):
        self.count += 1


        packet_manager.handle(self, buff, direction, name)


        if direction == "downstream":
            self.downstream.send_packet(name, buff.read())
        elif direction == "upstream":
            self.upstream.send_packet(name, buff.read())


    @defer.inlineCallbacks
    def connect(self):

        self.upstream_profile = yield Profile.from_credentials(EMAIL, PASSWORD)

        # token = ""
        # self.upstream_profile = yield Profile.from_token(client_token, token, display_name, uuid)


        self.upstream_factory = self.upstream_factory_class(
            self.upstream_profile)
        self.upstream_factory.bridge = self
        self.upstream_factory.force_protocol_version = \
            self.downstream.protocol_version
        self.upstream_factory.connect(
            self.connect_host,
            self.connect_port)



class QuietDownstreamFactory(DownstreamFactory):
    bridge_class = QuietBridge
    motd = "Proxy Server"


def main():
    # Create factory
    factory = QuietDownstreamFactory()

    factory.connect_host = "9b9t.com"
    factory.connect_port = 25565

    # Listen
    factory.listen("localhost", 25565)
    reactor.run()


if __name__ == "__main__":
    main()
