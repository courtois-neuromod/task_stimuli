# Push-To-Talk functions
import pulsectl

MIC_SOURCE_NAME = "alsa_input.pci-0000_00_1f.3.analog-stereo"
DSP_SINK_NAME = "dsp"
DSP_SINK_NAME = (
    "alsa_output.usb-Lenovo_ThinkPad_USB-C_Dock_Audio_000000000000-00.analog-stereo"
)


class PushToTalk:
    def __init__(self):
        self._pa_client = pulsectl.Pulse("ptt_loopback")
        self._source_idx = self._pa_client.get_source_by_name(MIC_SOURCE_NAME)
        self._sink_idx = self._pa_client.get_sink_by_name(DSP_SINK_NAME)

    def _init_loopback(self):
        self._loopback_mod_idx = self._pa_client.module_load(
            "module-loopback",
            "latency_msec=5 source=%d sink=%d" % (self._source_idx, self._sink_idx),
        )

    def _destroy_loopback(self):
        self._pa_client.unload_module(self._loopback_mod_idx)

    def mute(self):
        self._pa_client.source_mute(self._source_idx, 1)

    def unmute(self):
        self._pa_client.source_mute(self._source_idx, 0)
