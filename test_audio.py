import sounddevice as sd

print('Host APIs:')
wasapi_api = None
for hc, ha in enumerate(sd.query_hostapis()):
    print(f"[{hc}] {ha['name']}")
    if 'WASAPI' in ha['name']:
        wasapi_api = hc

print('---')
if wasapi_api is None:
    print('WASAPI not found!')
else:
    print(f'WASAPI is hostapi {wasapi_api}')

print('\nTesting loopback on all output devices:')
devices = sd.query_devices()
for idx, d in enumerate(devices):
    if d['max_output_channels'] > 0:
        ch = min(2, d['max_output_channels'])
        try:
            # First try the device as is, with WasapiSettings
            ws_settings = sd.WasapiSettings(loopback=True)
            s = sd.InputStream(
                device=idx, samplerate=44100, channels=ch, 
                extra_settings=ws_settings
            )
            print(f'SUCCESS: id={idx} {d["name"]} ch={ch}')
        except Exception as e:
            print(f'FAIL: id={idx} {d["name"]} Error: {e}')
