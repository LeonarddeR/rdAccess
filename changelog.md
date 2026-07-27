Incoming protocol messages are now handled synchronously on the IO thread in the order they arrive, instead of on a background thread pool. This eliminates a class of races where messages could be processed out of order or concurrently.
Rapid driver setting changes from the server (e.g. cycling voices in the synth settings ring) no longer lag or skip values: the client coalesces incoming setting changes and reports the newest value back, so the server's settings ring always steps from the actual current value.
Fixed a freeze when switching away from the remote synthesizer or braille display while the session is in a bad state, such as during a disconnect.
The client now rescans for channel pipes whenever the pipe directory changes, instead of relying on individual change events that Windows can drop during rapid reconnects. This fixes "Could not load the remote display/synthesizer" errors on the server when reconnecting in quick succession.
Protocol messages are now sent under a lock, preventing concurrent writes from different threads from corrupting the channel.
Hopefully fixed a bug in rd_pipe that caused the wrong virtual channel to be created.
The remote synthesizer and braille display drivers now initialize as soon as the channel is established, rather than waiting for the full attribute handshake. This makes connecting and reconnecting more reliable.
