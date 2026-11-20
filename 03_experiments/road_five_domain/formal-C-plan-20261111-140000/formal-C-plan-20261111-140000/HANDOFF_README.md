# 交接核验说明

训练、完整评价、独立指标与协议、主序对照、样例和图表在归档前已通过。包内STATUS在最终归档校验前冻结；最终完成以远端包外completion.json、handoff/handoff-verification.json及同名外置SHA为准，避免归档SHA自引用。接收后先核对归档SHA和安全成员路径，在新目录实际解包，核对MANIFEST及全文件集合/哈希。权重、原图、全量预测留远程，见remote-index.json。单seed顺序敏感性，不构成稳定排名。
