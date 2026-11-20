default_scope = 'mmseg'
custom_imports = dict(imports=[
    'road_dil',
])
model = dict(
    type='EncoderDecoder',
    data_preprocessor=dict(
        type='SegDataPreProcessor',
        mean=[
            123.675,
            116.28,
            103.53,
        ],
        std=[
            58.395,
            57.12,
            57.375,
        ],
        bgr_to_rgb=True,
        size=(
            512,
            512,
        ),
        pad_val=0,
        seg_pad_val=255,
        test_cfg=dict(size_divisor=32)),
    pretrained=None,
    backbone=dict(
        type='ResNetV1c',
        depth=101,
        in_channels=3,
        num_stages=4,
        base_channels=64,
        out_indices=(
            0,
            1,
            2,
            3,
        ),
        dilations=(
            1,
            1,
            1,
            1,
        ),
        strides=(
            1,
            2,
            2,
            2,
        ),
        norm_cfg=dict(type='BN', requires_grad=True),
        norm_eval=False,
        style='pytorch',
        contract_dilation=True),
    decode_head=dict(
        type='GS_AUFPN_Head',
        in_channels=[
            256,
            512,
            1024,
            2048,
        ],
        in_index=[
            0,
            1,
            2,
            3,
        ],
        channels=256,
        dropout_ratio=0.1,
        num_classes=19,
        mid_channels=128,
        N=64,
        reduction=16,
        kernel_size=3,
        norm_cfg=dict(type='BN', requires_grad=True),
        align_corners=False,
        loss_decode=dict(
            type='CrossEntropyLoss', use_sigmoid=False, loss_weight=1.0)),
    auxiliary_head=None,
    train_cfg=dict(),
    test_cfg=dict(mode='slide', crop_size=(
        512,
        512,
    ), stride=(
        341,
        341,
    )))
train_dataloader = dict(
    batch_size=2,
    num_workers=2,
    persistent_workers=True,
    sampler=dict(type='InfiniteSampler', shuffle=True),
    dataset=dict(
        type='RoadManifestDataset',
        ann_file=
        '/home/ysheng4/research/GSMF-RS-DIL/experiments/road_five_domain/prepare-20261111-140000/data/B_train.jsonl',
        data_prefix=dict(img_path='', seg_map_path=''),
        reduce_zero_label=False,
        ignore_index=255,
        test_mode=False,
        pipeline=[
            dict(type='LoadImageFromFile'),
            dict(type='LoadRoadAnnotations'),
            dict(
                type='RandomResize',
                scale=(
                    2048,
                    1024,
                ),
                ratio_range=(
                    0.5,
                    2.0,
                ),
                keep_ratio=True),
            dict(
                type='RandomCrop', crop_size=(
                    512,
                    512,
                ), cat_max_ratio=0.75),
            dict(type='RandomFlip', prob=0.5),
            dict(type='PhotoMetricDistortion'),
            dict(type='PackSegInputs'),
        ]))
val_dataloader = dict(
    batch_size=1,
    num_workers=2,
    persistent_workers=True,
    sampler=dict(type='DefaultSampler', shuffle=False),
    dataset=dict(
        type='RoadManifestDataset',
        ann_file=
        '/home/ysheng4/research/GSMF-RS-DIL/experiments/road_five_domain/prepare-20261111-140000/data/B_val.jsonl',
        data_prefix=dict(img_path='', seg_map_path=''),
        reduce_zero_label=False,
        ignore_index=255,
        test_mode=True,
        pipeline=[
            dict(type='LoadImageFromFile'),
            dict(type='LoadRoadAnnotations'),
            dict(type='PackSegInputs'),
        ]))
test_dataloader = dict(
    batch_size=1,
    num_workers=0,
    persistent_workers=False,
    sampler=dict(type='DefaultSampler', shuffle=False),
    dataset=dict(
        type='RoadManifestDataset',
        ann_file=
        '/home/ysheng4/research/GSMF-RS-DIL/experiments/road_five_domain/prepare-20261111-140000/data/D_val.jsonl',
        data_prefix=dict(img_path='', seg_map_path=''),
        reduce_zero_label=False,
        ignore_index=255,
        test_mode=True,
        pipeline=[
            dict(type='LoadImageFromFile'),
            dict(type='LoadRoadAnnotations'),
            dict(type='PackSegInputs'),
        ]))
val_evaluator = [
    dict(type='IoUMetric', iou_metrics=[
        'mIoU',
    ]),
    dict(type='RoadConfusionMetric'),
]
test_evaluator = [
    dict(type='IoUMetric', iou_metrics=[
        'mIoU',
    ]),
    dict(
        type='RoadConfusionMetric',
        output=
        '/home/ysheng4/research/GSMF-RS-DIL/experiments/road_five_domain/formal-B-plan-20261111-140000/eval-ft-seed1-D-snow/independent-metrics.json'
    ),
]
train_cfg = dict(type='IterBasedTrainLoop', max_iters=4000, val_interval=1000)
val_cfg = dict(type='ValLoop')
test_cfg = dict(type='TestLoop')
optim_wrapper = dict(
    type='OptimWrapper',
    optimizer=dict(
        type='AdamW', lr=1e-05, betas=(
            0.9,
            0.999,
        ), weight_decay=0.001),
    clip_grad=None)
param_scheduler = [
    dict(
        type='PolyLR',
        eta_min=0.0,
        power=0.9,
        begin=0,
        end=4000,
        by_epoch=False),
]
default_hooks = dict(
    timer=dict(type='IterTimerHook'),
    logger=dict(type='LoggerHook', interval=20, log_metric_by_epoch=False),
    param_scheduler=dict(type='ParamSchedulerHook'),
    checkpoint=dict(
        type='CheckpointHook',
        by_epoch=False,
        interval=1000,
        save_last=True,
        max_keep_ckpts=-1),
    sampler_seed=dict(type='DistSamplerSeedHook'))
custom_hooks = []
env_cfg = dict(
    cudnn_benchmark=False,
    mp_cfg=dict(mp_start_method='fork', opencv_num_threads=0),
    dist_cfg=dict(backend='nccl'))
visualizer = dict(
    type='SegLocalVisualizer',
    vis_backends=[
        dict(type='LocalVisBackend'),
    ],
    name='visualizer')
log_processor = dict(by_epoch=False)
log_level = 'INFO'
randomness = dict(seed=0, deterministic=True)
load_from = None
resume = False
work_dir = '/home/ysheng4/research/GSMF-RS-DIL/experiments/road_five_domain/formal-B-plan-20261111-140000/eval-ft-seed1-D-snow'
