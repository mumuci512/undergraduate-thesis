# MUSES

**[[Website]]**
**[[Paper]]**
**[[SDK]]**


MUSES, the MUlti-SEnsor Semantic perception dataset for driving under uncertainty is a multi-modal adverse condition dataset focused on 2D dense semantic perception.

It is composed of 2500 multi-modal scenes, each of which includes data from a frame camera, a lidar, a radar, an event camera, and an IMU/GNSS sensor. Each scene is accompanied by high-quality pixel-level panoptic annotations for the frame camera. The annotation process for MUSES utilizes all available sensor data, allowing the annotators to also reliably label degraded image regions that are still discernible in other modalities. This results in better pixel coverage in the annotations and creates a more challenging evaluation setup.
 
Further, each adverse-condition image comes with a corresponding image of the same scene taken under clear-weather, daytime conditions.
 
The dataset supports:
1. Panoptic segmentation
2. Uncertainty-aware panoptic segmentation
3. Semantic segmentation
4. Object detection

The ground-truth annotations of the training and validation sets are publicly available. The ground-truth annotations of the test set are withheld and they are used to establish the publicly available [MUSES benchmark].

We provide an [SDK] to read and process the sensor data.

### Download

MUSES can be downloaded through the associated [website][Website]. Users need to register on this website first before accessing the dataset.

Unzip all packages into the same folder:
```
unzip /path/to/downloaded_file.zip -d /path/to
```

You should get the following structure:
```
muses/
├── frame_camera
├── gt_panoptic
├── gt_uncertainty
├── gt_semantic
├── gt_detection
├── lidar
├── radar
├── event_camera
├── reference_frames
├── gnss
├── calib.json
├── meta.json
├── LICENSE.pdf
└── README.md
```

To work with a subset of the dataset, (i.e. standard panoptic segmentation on RGB) you can download only the relevant folders:
```
muses/
├── gt_panoptic
├── frame_camera
├── meta.json
├── LICENSE.pdf
└── README.md
```

**Note**: Due to data protection regulations, only anonymized versions of the images are available.

### Dataset Structure

The directory structure of MUSES is as follows:
```
{root}/{type}/{split}/{weather_condition}/{time_of_day}/{sequence}_frame_{frame:0>6}_{type}.{ext}
```
The meaning of the individual directory levels is:
 - `root`      the root directory where the dataset is stored.
 - `type`      the type/modality of data, e.g. `frame_camera` for the frame-camera RGB images, or `gt_panoptic` for ground-truth panoptic annotations.
 - `split`     the split, e.g. `train`. Note that not all types of data exist for all splits.
 - `weather_condition` the weather condition associated with the data, e.g. `clear`.
 - `time_of_day` the time of day associated with the data, e.g. `day`.
 - `sequence`  the recording sequence, e.g. `REC0176`.
 - `frame:0>6` the frame number within the respective sequence, composed of six digits.
 - `ext`       the file extension, e.g. `png` for images.

Possible values of `type`:
- `frame_camera`: RGB images from the frame camera.
- `lidar`: point cloud data from the lidar sensor.
- `radar`: radar data.
- `event_camera`: 30ms of events from the event camera ahead of the exposure-end-timestamps of the frame camera.
- `event_camera_3s`: full 3s of events from the event camera ahead of the exposure-end-timestamps of the frame camera.
- `gnss`: IMU/GNSS data.
- `reference_frames`:  corresponding clear-weather and daytime reference images recorded at the same location as the adverse-condition frame camera images. These image only exists for adverse-condition frame camera images (every condition except `clear` + `day`).
- `gt_panoptic`: ground-truth panoptic segmentation annotations.
- `gt_semantic`: ground-truth semantic segmentation annotations.
- `gt_uncertainty`: ground-truth uncertainty annotations for uncertainty-aware panoptic and semantic segmentation.
- `gt_detection`: ground-truth object detection annotations.

Possible values of `split`:
- `train`
- `val`
- `test`

Possible values of `weather_condition`:
- `clear`
- `fog`
- `rain`
- `snow`

Possible values of `time_of_day`:
- `day`
- `night`

Possible values of `ext`:
- `png`: for images and raw radar data.
- `h5`: for events.
- `bin`: for lidar point clouds.

### Dataset Structure for Annotations

#### Panoptic Segmentation Annotations
The provided **panoptic segmentation** annotations  in the `gt_panoptic` folder generally follow the [COCO format]. 

The directory structure of MUSES panoptic segmentation annotations is as follows:

```
├── train
│   ├── clear
│   │   ├── day
│   │   ├── night
│   ├── rain
│   │   ├── day
│   │   ├── night
│   ├── snow
│   │   ├── day
│   │   ├── night
│   ├── fog
│   │   ├── day
│   │   ├── night
├── val
│   ├── clear
│   │   ├── day
│   │   ├── night
│   ├── rain
│   │   ├── day
│   │   ├── night
│   ├── snow
│   │   ├── day
│   │   ├── night
│   ├── fog
│   │   ├── day
│   │   ├── night
├── test_image_info.json
├── train.json
├── val.json
└── gt_panoptic_by_condition
    ├── gt_panoptic json files by split, condition and time_of_day
    ├── ...
```

For panoptic segmentation, the semantic annotation json files for specific conditions are placed in the path 
```
{root}/gt_panoptic/gt_panoptic_by_condition/{split}_{condition}.json`
```

Here `condition` is optional. It could be any combination of `{weather_condition}_{time_of_day}`, also with either of them empty.
e.g. 
- `train_clear_day.json`, for the train split of the clear day condition
- `val_fog.json` for the val split of all fog condition (independent of time of day), or
- `val_day.json` for the val split of all day condition (independent of weather)

The pixel-level panoptic mask PNG files are placed in the path 
```
{root}/gt_panoptic/{split}/{weather_condition}/{time_of_day}/{sequence}_frame_{frame:0>6}_gt_panoptic.png`
```

To include our additional sensors and annotations, we adapted the panoptic annotation json files to include the following fields:
```
"annotations":[{
    "image_id": "{sequence}_frame_{frame:0>6}_frame_camera",
    "file_name": "{split}/{weather_condition}/{time_of_day}/{sequence}_frame_{frame:0>6}_gt_panoptic.png",
    "gt_uncertainty_file_name": "{split}/{weather_condition}/{time_of_day}/{sequence}_frame_{frame:0>6}_gt_uncertainty.png",
    "segments_info": [{...}, ...],
    },...]
```
```
"images"::[{
            "id": "{sequence}_frame_{frame:0>6}_frame_camera",
            "file_name": "{split}/{weather_condition}/{time_of_day}/{sequence}_frame_{frame:0>6}_frame_camera.png",
            "event_camera_file_name": "{split}/{weather_condition}/{time_of_day}/{sequence}_frame_{frame:0>6}_event_camera.h5",
            "event_camera_file_3s_name": "{split}/{weather_condition}/{time_of_day}/{sequence}_frame_{frame:0>6}_event_camera_3s.h5",
            "gnss_file_name": "{split}/{weather_condition}/{time_of_day}/{sequence}_frame_{frame:0>6}_gnss.txt",
            "lidar_file_name": "{split}/{weather_condition}/{time_of_day}/{sequence}_frame_{frame:0>6}_lidar.bin",
            "radar_file_name": "{split}/{weather_condition}/{time_of_day}/{sequence}_frame_{frame:0>6}_radar.png",
            "reference_frame_file_name": "{split}/{weather_condition}/{time_of_day}/{sequence}_frame_{frame:0>6}_reference_frame.png",
            "height": 1080,
            "width": 1920,
        },
    ...}, ...],
```
#### Uncertainty Annotations

The provided **uncertainty** annotations in the `gt_uncertainty` folder result from our two-step annotation protocol. 

The path to each uncertainty-level annotation mask is provided in the panoptic annotation files `gt_panoptic/{split}.json` under `gt_uncertainty_file_name`.

```
{root}/gt_uncertainty/{split}/{weather_condition}/{time_of_day}/{sequence}_frame_{frame:0>6}_gt_uncertainty.png`
```

Each pixel in the uncertainty annotation mask is assigned a ternary *uncertainty* level, which is encoded as follows:
- `certain` (0): pixels with certain class and, if relevant, instance.
- `uncertain_instance` (127, grey): pixels with a certain class label, but an uncertain instance label.
- `uncertain_class` (255, white): pixels with an uncertain class label.

#### Detection Annotations

The provided **detection** annotations in the `gt_detection` folder follow the [COCO format].

The directory structure of MUSES detection annotations folder is as follows:

```
├── instancesonly_train.json
├── instancesonly_val.json
├── instancesonly_test_image_info.json
└── gt_detection_by_condition
    ├── instancesonly_{split}_{condition}.json files by split, weather_condition and time_of_day
    ├── ...
```

`gt_detection` refers to ground-truth annotations, which is relevant for the `train` and `val` splits.
`image_info` only contains the list of images and the predefined categories, which is relevant for the `test` split. 

The detection annotation json files for specific conditions are placed in the path 
```
{root}/gt_detection/gt_detection_by_condition/{split}_{condition}.json`
```
Here `condition` is optional. It could be any combination of `{weather_condition}_{time_of_day}`, also with either of them empty.


#### Semantic Segmentation Annotations

The provided **semantic** annotations are located in the `gt_semantic` folder.

The MUSES semantic segmentation annotations are stored as follows:

```
{root}/gt_semantic/{split}/{weather_condition}/{time_of_day}/{sequence}_frame_{frame:0>6}_{suffix}.png
```

Possible values of `suffix`:
 - `labelIds`      semantic labels encoded using `png` images, where pixel values encode labels in Cityscapes IDs format. Please refer to the script [helpers/labels.py][cityscapes_labels_docs] in the [Cityscapes GitHub repository][cityscapesGithub] for details on the 19 semantic classes included in our semantic annotations, which coincide with the classes that are included in Cityscapes evaluation.
 - `labelTrainIds` semantic labels encoded using `png` images, where pixel values encode labels in Cityscapes trainIDs format.
 - `labelColor`    semantic labels encoded using `png` images, where pixel values encode labels in Cityscapes color format. Purposed for visualization.


### Sensor Data

The selected combination of sensor data provides a comprehensive view of the driving environment, capturing a wide range of information that can be used to enhance the performance of perception systems.  The frame camera provides high-resolution RGB images, capturing the visual appearance of the scene. The lidar sensor provides 3D point cloud data, offering depth information and enabling the detection of objects even in low-light conditions. The radar sensor provides robust distance information about surrounding objects, which is particularly useful in adverse weather conditions where other sensors may struggle. The event camera captures changes in the scene at a high temporal resolution, making it ideal for detecting fast-moving objects. As the event data is very memory-intensive, we provide both a 30ms and a 3s version. Finally, the IMU/GNSS sensor provides precise localization information for ego-motion compensation. 

The sensor data is stored in the following format:
- Frame camera images are stored as PNG files.
- Lidar point clouds are stored as binary files in the PCD format.
- Radar scans are stored as PNG files.
- Event camera data are stored as HDF5 files.
- IMU/GNSS data are stored as text files, according to the format file: `gnss/dataformat.txt`

We provide an [SDK] on github with exemplar scripts to read and process the sensor data. Please refer to the [SDK] for more information.

### Metadata

In each package available for download, we also include a `meta.json` file which provides additional information about each scene. These metadata are amenable to processing with our SDK and provide additional context about the conditions under which each scene was captured, including weather, time of day, exact timestamps, and paths to respective sensor recordings and annotations.

### Evaluation

Please refer to the [SDK] for an exemplar script for evaluating our novel task of uncertainty-aware panoptic segmentation, using our average uncertainty-aware panoptic quality, or **AUPQ**, metric. We use a similar script to evaluate submissions to the [MUSES benchmark] for this task.

### Citation

If you use MUSES in your work, please cite our publications as listed on the [MUSES website][muses_citation].

### License

MUSES is made available for non-commercial use under the license agreement which is contained in the attached file `License.pdf`.

### Contact

Please feel free to contact us with any questions or comments:

Tim Broedermann, David Bruggemann, and Christos Sakaridis

E-Mail: muses[dot]efcl[at]zohomail[dot]eu

Website: https://muses.vision.ee.ethz.ch

[Website]: <https://muses.vision.ee.ethz.ch>
[MUSES benchmark]: <https://muses.vision.ee.ethz.ch/benchmarks>
[muses_citation]: <https://muses.vision.ee.ethz.ch/citation>
[cityscapesGithub]: <https://github.com/mcordts/cityscapesScripts>
[cityscapes_labels_docs]: <https://github.com/mcordts/cityscapesScripts/blob/master/cityscapesscripts/helpers/labels.py>
[COCO format]: <https://cocodataset.org/#format-data>
[SDK]: <https://github.com/timbroed/MUSES>
[Paper]: <https://arxiv.org/pdf/2401.12761.pdf>