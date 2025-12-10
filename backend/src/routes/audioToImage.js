const express = require('express');
const doubaoService = require('../services/doubaoService');

function audioToImageRoute(upload) {
  const router = express.Router();

  /**
   * POST /api/audio-to-image
   * 接收音频文件，转换为文字，再生成图片
   */
  router.post('/audio-to-image', upload.single('audio'), async (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ error: '未收到音频文件' });
      }

      const audioBuffer = req.file.buffer;
      const audioFormat = req.file.mimetype.split('/')[1] || 'wav';

      console.log(`📥 收到音频文件: ${req.file.size} bytes, 格式: ${audioFormat}`);

      // 检查API密钥
      const hasApiKey = !!process.env.DOUBAO_API_KEY;
      
      // 步骤1: 语音转文字
      console.log('🔄 开始语音转文字...');
      let text;
      if (hasApiKey) {
        text = await doubaoService.audioToText(audioBuffer, audioFormat);
      } else {
        console.log('⚠️  使用模拟API（未配置DOUBAO_API_KEY）');
        text = await doubaoService.mockAudioToText(audioBuffer);
      }
      console.log(`✅ 识别文字: ${text}`);

      // 步骤2: 文字生成图片
      console.log('🎨 开始生成图片...');
      let imageResult;
      if (hasApiKey) {
        imageResult = await doubaoService.textToImage(text);
      } else {
        console.log('⚠️  使用模拟API（未配置DOUBAO_API_KEY）');
        imageResult = await doubaoService.mockTextToImage(text);
      }
      console.log('✅ 图片生成完成');

      // 返回结果
      res.json({
        success: true,
        text: text,
        imageUrl: imageResult.imageUrl,
        imageData: imageResult.imageData,
        timestamp: new Date().toISOString()
      });

    } catch (error) {
      console.error('处理错误:', error);
      res.status(500).json({
        success: false,
        error: error.message || '处理失败，请稍后重试'
      });
    }
  });

  return router;
}

module.exports = audioToImageRoute;

