# GoodFocus

GoodFocus is an automatic personalized educational intervention system using human feedback, accompanied by EEG and LLM agents. This is an upload of all scripts used in GoodFocus. 

Recordings of the experimental data collection and the EEG data and logs of the script running are [here.](https://drive.google.com/drive/folders/13nDVU8tmVHbasHnjL6Imr7m3hWpLcV1_?usp=sharing)

## Usage 

Unless you have the original hardware used in the experiment, to use GoodFocus, you must modify ```./extract.py``` to suit your own needs. The EEG hardware originally called the function ```def attention_callback(attention_value):``` every second on a seperate thread with an ```attention_value``` in the range $0\le attentionValue\le 100$ (from inattentive to attentive). A warning: GoodFocus wasn't made as a library or with other collaborators or code contributers in mind. Read the markdown file in ```./PACE_data/``` for more details. Good luck.

## License

All parts of GoodFocus (except for ./neuro/Neuro.py and quiz bowl questions collected from PACE released publicly [here](https://quizbowlpackets.com/)) is under the Apache License, Version 2.0.
