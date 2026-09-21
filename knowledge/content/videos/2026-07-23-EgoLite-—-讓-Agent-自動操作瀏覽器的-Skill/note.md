---
title: "EgoLite — 讓 Agent 自動操作瀏覽器的 Skill"
url: https://www.bilibili.com/video/BV1aDKb6pEnJ/
source: bilibili
transcript_kind: asr
reliability: asr
date: 2026-07-23
tags: []
---

## 重點摘要：EgoLite — 讓 AI Agent 接管瀏覽器的 Skill（技術爬爬蝦）

**一句話**：EgoLite 是基於 Chromium 的瀏覽器，讓 AI agent 和人共用同一個瀏覽器、複用登入態，搭配它的 skill 讓 Claude Code / agent 又快又省 token 完成瀏覽器重複操作，流程固化成腳本後可零 token 全自動。

### 解決的痛點（vs Playwright/Puppeteer）
反覆登入、記憶體占用大、token 高、執行慢。對策：
- **複用登入態**：匯入 Chrome cookie/密碼/Profile（本地離線）→ agent 直接用你的登入，不用再登入。
- **space 架構**：每個 space 獨立工作空間，agent 控藍色的、你控其餘，互不干擾，可並行；記憶體/進程開銷官方稱比傳統低數十倍。
- **少來回省 token**：Claude Code 把所有操作寫進一段 Node.js heredoc 一次送瀏覽器執行，降低模型↔瀏覽器交互次數。

### 用法
Mac 版免費；Claude Code 輸入 `EgoBrowser` 呼叫，首次自動掃描已裝 agent、零設定塞 skill。流程可「固化成 skill」（約 4 倍效率），再讓 agent 寫成腳本 → 命令列跑、零 token。

### 示範
ChatGPT 生資訊圖（開 10 個 space 並行）、抓競品 100 則評論→CSV（再固化成 JS 腳本零 token 重跑）、行程規劃（3 space 並行查票務/天氣/攻略）、找工作（百度地圖+招聘網→離家近 20 職缺按距離排序→CSV）。

**與 rivendell 相關**：這是「用 skill 封裝 agent 能力」的實例，跟本專案 skills 同思路，EgoLite 這工具值得留意。

## 逐字稿

> `transcript.txt` (same folder) — 完整版。以下為前導：

这个skill能给任意的AA Agent接入顶级的浏览器自动化能力
帮你完成各种机械重复的操作
本期视频我们使用的工具是EgoLite还有配套的skill
EgoLite是一个基于Chronium内核开发的全新浏览器
核心设计理念上Agent和人类能共用同一个Chrome进行流畅协作
EgoLite通过全新的架构设计
针对传统浏览器自动化工具里面反复登录
内存占用大,token消耗高,执行速度慢等几大通点都进行了明显优化
本期视频带来一个手把手的完整教程
我们看看怎么在Cloud Code,workbody等各种AA Agent里面接入EgoLite
熟练使用以后我们还能把很多工作流程沉淀成可复用的skill
让AA能够又快又省的完成任务
甚至还有许多固定流程只需要让AA编写好一个脚本
就能全程脱离AA参与,零token全自动完成工作
好,废话不多说,我们直接开始
我们先去EgoLite官网把浏览器下载一下
目前上线的是麦克版本,完全的免费使用
下载完成以后打开安装文件,托转进来就完成了安装
EgoLite第一次启动的时候会询用我是否导入之前的浏览器配置
这里我选择Chrome
导入以后我的Chrome上所有的网站登录状态
Cookie、X键、Profile等数据都迁移到了EgoLite
这些数据都是离线保存在本地设备上的
后续AA的自动化操作都可以附用这些登录态
彻底解决了传统浏览器自动化的痛点之一
也就是重复登录的问题
接下来我们来测试一下
这里我先用Cloud Code接入
打开中端输入Cloud来启动Cloud Code
进来以后我们可以直接敲鞋线EgoBrowser
调用EgoLite的skill
EgoLite第一次启动的时候会自动扫描电脑上已经安装的Agent
自动把skill存放到Agent的对应目录里面
零配置就能使用它的skill 非常的方便
淮巴侠最近经常让chatgbt帮我画一些信息图
作为补充材料插到视频里面去用
传统方法需要打开chatgbt的对话框
点击创建图片
然后填入提示词
等待图片生成最后下载
