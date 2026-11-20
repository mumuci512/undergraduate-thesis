# Quick Start Guide

## Standard Panoptic Segmentation (RGB Image Based)
For standard frame camera based panoptic segmentation, download the following packages:

- Panoptic Annotations [trainval]
- Panoptic Annotations [test]
- RGB Frame Camera [trainvaltest]

## Uncertainty-Aware Panoptic Segmentation (RGB Image Based)
For uncertainty-Aware panoptic segmentation using the RGB camera, download the following packages:

- Panoptic Annotations [trainval]
- Panoptic Annotations [test]
- RGB Frame Camera [trainvaltest]
- Uncertainty Annotations [trainval]

## Multi-modal Panoptic Segmentation
For multi-modal panoptic segmentation, download the following packages:

- Panoptic Annotations [trainval]
- Panoptic Annotations [test]
- RGB Frame Camera [trainvaltest]
- Lidar [trainvaltest]
- Radar [trainvaltest]
- Event Camera [trainvaltest]
- GNSS [trainvaltest]

## Other Tasks (Object Detection/Semantic Segmentation)
For other tasks like object detection and semantic segmentation, download the corresponding annotation packages instead of the panoptic annotations:

- Semantic Annotations [trainval]
- Object Detection Annotations [trainval]

## How to Unpack the Zip Files
After downloading the packages, run this command for each package to unpack the zip files into the same location:

```bash
unzip /path/to/file.zip -d /path/to/data
```
                
The output will look like /path/to/data/muses/[type of package]. Each package also includes a README, license file, meta.json, and calib.json. For further information please refer to the README of the downloaded packages and the [MUSES SDK](https://github.com/timbroed/MUSES).

## Codabench Benchmarks
The benchmark evaluates segmentation on MUSES across clear and adverse conditions. Submissions are scored on a private, unreleased test set and shown on the public leaderboard.
- **[Panoptic Segmentation](https://www.codabench.org/competitions/13987/)** 
- **[Semantic Segmentation](https://www.codabench.org/competitions/14005/)** 
