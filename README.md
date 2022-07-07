Tabula Synthesizer

This repository contains the task planner for Tabula.

# Installation

## Prerequisites

- Ubuntu 20.04
- an installation of python3 and java
- ROS Noetic (optional)

If on a ROS computer, do the following (TO BE ADDED).

If not on a ROS computer, do the following:

```
git clone git@github.com:dporfirio/TabulaSynthesizer.git
cd TabulaSynthesizer
mkdir bin && cd bin
wget https://nlp.stanford.edu/software/stanford-corenlp-latest.zip
unzip stanford-corenlp-latest.zip
```

# Running

Before running, the Stanford CoreNLP server must be started.

```
java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -port 9000 -timeout 15000
```

To run the test cases, do the following:

```
cd synthesizer/src
./test.bash
```
