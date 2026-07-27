Fixed a freeze when switching away from the remote synthesizer or braille display while the session is in a bad state, such as during a disconnect.
Protocol messages are now sent under a lock, preventing concurrent writes from different threads from corrupting the channel.
Hopefully fixed a bug in rd_pipe that caused the wrong virtual channel to be created.
The remote synthesizer and braille display drivers now initialize as soon as the channel is established, rather than waiting for the full attribute handshake. This makes connecting and reconnecting more reliable.
