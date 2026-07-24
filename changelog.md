Hopefully fixed a bug in rd_pipe that caused the wrong virtual channel to be created.
The remote synthesizer and braille display drivers now initialize as soon as the channel is established, rather than waiting for the full attribute handshake. This makes connecting and reconnecting more reliable.
