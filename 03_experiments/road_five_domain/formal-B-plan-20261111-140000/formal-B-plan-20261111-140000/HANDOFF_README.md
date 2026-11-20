# 交接核验说明

所有训练、完整评价、独立指标与协议复核、样例和图表在归档前已通过。包内STATUS在最终归档校验前冻结，故仍写待打包核验；最终完成以远端包外completion.json、handoff/handoff-verification.json及同名外置SHA为准。这样避免归档SHA自引用。接收后仍应先检查归档SHA、安全成员路径，再在新目录实际解包并核对MANIFEST.sha256及文件集合。权重、原图、全量预测留远端，见remote-index.json。阶段C未授权。
