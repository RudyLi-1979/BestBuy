# Gradle 版本相容性說明

## 版本資訊

- **Gradle**: 8.7
- **Android Gradle Plugin (AGP)**: 8.3.2
- **Kotlin**: 1.9.23
- **Java**: 支援 Java 21
- **最低 Android SDK**: API 24 (Android 7.0)
- **目標 Android SDK**: API 34 (Android 14)

## 相容性矩陣

| 元件 | 版本 | 說明 |
|------|------|------|
| Gradle | 8.7 | 支援 Java 21 |
| AGP | 8.3.2 | 與 Gradle 8.5+ 相容 |
| Kotlin | 1.9.23 | 最新穩定版 |
| Java | 8 - 21 | 建議使用 Java 17 或 21 |

## 更新說明

### 從 Gradle 8.0 升級到 8.7

**原因**: Gradle 8.0 不支援 Java 21

**變更內容**:
1. ✅ 更新 `gradle-wrapper.properties` - Gradle 8.7
2. ✅ 更新 `build.gradle.kts` - AGP 8.3.2
3. ✅ 更新 Kotlin 版本 - 1.9.23
4. ✅ 優化 `gradle.properties` - 增加記憶體和啟用快取

### 效能優化

`gradle.properties` 中的新增設定：
```properties
org.gradle.caching=true           # 啟用建置快取
org.gradle.parallel=true          # 並行建置
org.gradle.configureondemand=true # 按需配置
kotlin.incremental=true           # 增量編譯
```

## 如何同步專案

### 方法 1: Android Studio
1. 點擊 **File** → **Invalidate Caches / Restart**
2. 重啟後，點擊 **Sync Now**

### 方法 2: 命令列
```bash
# Windows
gradlew clean build

# 或強制更新依賴
gradlew clean build --refresh-dependencies
```

### 方法 3: 清除快取
```bash
# 清除 Gradle 快取
gradlew cleanBuildCache

# 完整清理
gradlew clean
```

## 常見問題

### Q: 為什麼選擇 Gradle 8.7 而不是 9.0？
A: Gradle 9.0 目前還在 milestone 階段，8.7 是最新的穩定版本，更適合生產環境。

### Q: Java 版本要求？
A: 
- **Gradle 8.7**: 支援 Java 8 到 21
- **推薦**: Java 17 或 Java 21（LTS 版本）
- **最低**: Java 8

### Q: 同步失敗怎麼辦？
A: 
1. 檢查網路連線
2. 清除 Gradle 快取：`gradlew clean`
3. 刪除 `.gradle` 資料夾並重新同步
4. 確認 Java 版本：`java -version`

### Q: 記憶體不足錯誤？
A: 調整 `gradle.properties` 中的記憶體設定：
```properties
org.gradle.jvmargs=-Xmx4096m
```

## 驗證安裝

執行以下命令確認版本：

```bash
# 檢查 Gradle 版本
gradlew --version

# 檢查 Java 版本
java -version

# 測試建置
gradlew assembleDebug
```

## 升級檢查清單

- [x] ✅ Gradle 升級到 8.7
- [x] ✅ AGP 升級到 8.3.2
- [x] ✅ Kotlin 升級到 1.9.23
- [x] ✅ gradle.properties 性能優化
- [ ] 🔄 清除快取並重新同步
- [ ] 🔄 測試建置

## 疑難排解

### 錯誤: "Could not download gradle-8.7-bin.zip"

**解決方案**:
```bash
# 手動下載 Gradle
# 1. 訪問: https://services.gradle.org/distributions/gradle-8.7-bin.zip
# 2. 下載後放到: %USERPROFILE%\.gradle\wrapper\dists\gradle-8.7-bin\
```

### 錯誤: "Unsupported class file major version"

**解決方案**:
- 確保使用的 Java 版本與 Gradle 相容
- 檢查 JAVA_HOME 環境變數

### 建置很慢

**解決方案**:
1. 增加 `gradle.properties` 中的記憶體
2. 啟用 Gradle daemon
3. 使用 SSD 硬碟
4. 關閉防毒軟體對專案資料夾的即時掃描

## 參考資料

- [Gradle 8.7 Release Notes](https://docs.gradle.org/8.7/release-notes.html)
- [AGP 8.3 Release Notes](https://developer.android.com/studio/releases/gradle-plugin)
- [Kotlin 1.9.23 What's New](https://kotlinlang.org/docs/whatsnew1923.html)
- [Java 21 Compatibility](https://docs.gradle.org/current/userguide/compatibility.html)

---

**注意**: 升級後首次同步可能需要較長時間，因為 Gradle 需要下載新版本和依賴項。
