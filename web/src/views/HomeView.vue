<template>
  <div class="home" :style="cssVars">
    <div v-if="isLoading" class="state state--loading" aria-live="polite">
      <a-spin size="large" />
      <p class="state-text">正在连接服务...</p>
    </div>

    <div v-else-if="error" class="state state--error">
      <a-result status="error" :title="error.title" :sub-title="error.message">
        <template #extra>
          <a-button type="primary" @click="retryLoad" aria-label="重试连接">重试</a-button>
          <a-button
            :href="faqUrl"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="打开常见问题"
          >
            常见问题
          </a-button>
        </template>
      </a-result>
    </div>

    <template v-else>
      <header class="topbar" aria-label="首页顶栏">
        <div class="topbar-inner">
          <a class="brand" href="/" @click.prevent="goHome" aria-label="返回首页">
            <img
              v-if="brandLogoUrl"
              class="brand-logo"
              :src="brandLogoUrl"
              :srcset="brandLogoSrcset"
              :alt="orgName || brandName"
              loading="lazy"
              decoding="async"
            />
            <div class="brand-text">
              <span class="brand-name">{{ brandName }}</span>
            </div>
          </a>

          <div class="topbar-actions">
            <button
              v-if="!isLoggedIn"
              class="topbar-login"
              type="button"
              aria-label="登录"
              @click="goLogin"
            >
              登录
            </button>
            <UserInfoComponent v-else :show-button="true" />
          </div>
        </div>
      </header>

      <main class="main" aria-label="首页内容">
        <section class="hero" aria-label="欢迎区">
          <div class="hero-inner">
            <div class="hero-left">
              <p class="hero-eyebrow">{{ heroEyebrow }}</p>
              <h1 class="hero-title">
                <span class="hero-title-main">{{ heroTitle }}</span>
                <span class="hero-title-accent">{{ heroSubtitle }}</span>
              </h1>
              <p class="hero-description">
                {{ heroDescription }}
              </p>
              <div class="hero-actions">
                <button class="cta" type="button" @click="goToChat" aria-label="开始使用">
                  开始使用
                  <span class="cta-arrow" aria-hidden="true">→</span>
                </button>
              </div>
            </div>

            <div class="hero-right" aria-label="产品预览">
              <div class="hero-frame" aria-label="产品预览图">
                <div class="hero-frame-bar" aria-hidden="true"></div>
                <img
                  class="hero-image"
                  :src="heroImageUrl"
                  :srcset="heroImageSrcset"
                  alt="产品界面预览"
                  loading="lazy"
                  decoding="async"
                />
              </div>
            </div>
          </div>
        </section>

        <section class="capabilities" aria-label="能力介绍">
          <div class="cap-grid">
            <article v-for="item in capabilityCards" :key="item.title" class="cap-card">
              <img
                class="cap-icon"
                :src="item.icon"
                :srcset="item.iconSrcset"
                :alt="item.title"
                loading="lazy"
                decoding="async"
              />
              <h3 class="cap-title">{{ item.title }}</h3>
              <p class="cap-desc">{{ item.description }}</p>
            </article>
          </div>
        </section>
      </main>

      <footer class="footer" aria-label="页脚">
        <p class="footer-text">{{ footerCopyright }}</p>
      </footer>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useInfoStore } from '@/stores/info'
import { useAgentStore } from '@/stores/agent'
import { healthApi } from '@/apis/system_api'
import UserInfoComponent from '@/components/UserInfoComponent.vue'
import { useThemeStore } from '@/stores/theme'

const router = useRouter()
const userStore = useUserStore()
const infoStore = useInfoStore()
const agentStore = useAgentStore()
const themeStore = useThemeStore()
const faqUrl = 'https://xerrors.github.io/Yuxi/' // info.template.yaml 未提供该链接字段，保留默认值

const isLoading = ref(true)
const error = ref(null)

const infoConfig = ref(null)

const normalizeAssetUrl = (url) => {
  const text = (url || '').trim()
  if (!text) return ''
  if (/^(https?:)?\/\//i.test(text)) return text
  if (text.startsWith('/')) return encodeURI(text)
  return encodeURI(`/${text}`)
}

const isLoggedIn = computed(() => userStore.isLoggedIn)

const organization = computed(() => infoConfig.value?.organization || {})
const branding = computed(() => infoConfig.value?.branding || {})
const footer = computed(() => infoConfig.value?.footer || {})

const orgName = computed(() => (organization.value.name || '').trim())
const brandName = computed(() => (branding.value.name || '').trim())

const theme = computed(() => {
  const t = infoConfig.value?.theme || {}
  return {
    primary: (t.primary || '#1d5eff').trim(), // info.template.yaml 未提供 theme 字段，保留默认值
    primaryHover: (t.primary_hover || '#1a52e6').trim(), // info.template.yaml 未提供 theme 字段，保留默认值
    heroBg: (t.hero_bg || '#eaf3ff').trim() // info.template.yaml 未提供 theme 字段，保留默认值
  }
})

const heroEyebrow = computed(() => {
  const text = infoConfig.value?.home?.hero_eyebrow
  return (text || '企业级知识库管理平台').trim() // info.template.yaml 未提供 home.hero_eyebrow 字段，保留默认值
})

const heroTitle = computed(() => (branding.value.title || '').trim())
const heroSubtitle = computed(() => (branding.value.subtitle || '').trim())

const heroDescription = computed(() => {
  const text = infoConfig.value?.home?.hero_description
  if (typeof text === 'string' && text.trim()) {
    return text.trim()
  }
  const subs = branding.value.subtitles
  if (Array.isArray(subs) && subs.length) {
    const first = (subs[0] || '').trim()
    if (first) return first
  }
  return '为企业提供专业的知识管理解决方案，让知识沉淀更简单，让信息触达更高效。' // info.template.yaml 未提供 home.hero_description 字段，保留默认值
})

const brandLogoUrl = computed(() => normalizeAssetUrl(organization.value.logo || ''))
const brandLogoSrcset = computed(() => {
  const base = brandLogoUrl.value
  const retina = normalizeAssetUrl('/维盈logo 2@2x.png')
  if (!base) return ''
  return retina ? `${base} 1x, ${retina} 2x` : ''
})

const heroImageUrl = computed(() => {
  const custom = infoConfig.value?.home?.hero_image
  return normalizeAssetUrl(custom || '/container12.png') // info.template.yaml 未提供 home.hero_image 字段，保留默认值
})
const heroImageSrcset = computed(() => {
  const base = heroImageUrl.value
  const retina = normalizeAssetUrl('/container12(2).png')
  if (!base) return ''
  return retina ? `${base} 1x, ${retina} 2x` : ''
})

const footerCopyright = computed(() => {
  const text = footer.value.copyright
  return (text || '© 中国电信（江西）工业互联网研究院').replace(/\s+\d{4}\s+v\S+\s*$/i, '').trim()
})

const defaultCapabilityCards = [
  {
    title: '知识共享',
    description: '打破信息孤岛，促进知识在组织内自然流动与沉淀。',
    icon: normalizeAssetUrl('/Container11.png'),
    iconSrcset: `${normalizeAssetUrl('/Container11.png')} 1x, ${normalizeAssetUrl('/Container11(2).png')} 2x`
  },
  {
    title: '开放协作',
    description: '鼓励团队协作共建，让每个人都成为知识贡献者。',
    icon: normalizeAssetUrl('/Container(2).png'),
    iconSrcset: `${normalizeAssetUrl('/Container(2).png')} 1x, ${normalizeAssetUrl('/Container@2x(2).png')} 2x`
  },
  {
    title: '持续创新',
    description: '不断迭代知识管理能力，引入前沿 AI 技术赋能业务。',
    icon: normalizeAssetUrl('/Container(3).png'),
    iconSrcset: `${normalizeAssetUrl('/Container(3).png')} 1x, ${normalizeAssetUrl('/Container@2x(3).png')} 2x`
  },
  {
    title: '安全可靠',
    description: '严格的权限管理和数据保护，确保知识资产安全。',
    icon: normalizeAssetUrl('/Container(4).png'),
    iconSrcset: `${normalizeAssetUrl('/Container(4).png')} 1x, ${normalizeAssetUrl('/Container@2x(4).png')} 2x`
  },
  {
    title: '多格式支持',
    description: '支持 PDF、Word、Markdown、图片等多种格式，快速导入知识。',
    icon: normalizeAssetUrl('/Container(5).png'),
    iconSrcset: `${normalizeAssetUrl('/Container(5).png')} 1x, ${normalizeAssetUrl('/Container@2x(5).png')} 2x`
  },
  {
    title: '知识图谱构建',
    description: '自动化 LightRAG 助手构建知识图谱，用于智能体推理。',
    icon: normalizeAssetUrl('/Container(6).png'),
    iconSrcset: `${normalizeAssetUrl('/Container(6).png')} 1x, ${normalizeAssetUrl('/Container@2x(6).png')} 2x`
  },
  {
    title: 'RAG 检索增强',
    description: '基于检索增强生成技术，提供精准的知识问答能力。',
    icon: normalizeAssetUrl('/Container(7).png'),
    iconSrcset: `${normalizeAssetUrl('/Container(7).png')} 1x, ${normalizeAssetUrl('/Container@2x(7).png')} 2x`
  },
  {
    title: '智能体系统',
    description: '支持多智能体协同与子智能体协作，处理更复杂场景。',
    icon: normalizeAssetUrl('/Container(8).png'),
    iconSrcset: `${normalizeAssetUrl('/Container(8).png')} 1x, ${normalizeAssetUrl('/Container@2x(8).png')} 2x`
  }
] // info.template.yaml 未提供 home.capability_cards 字段，保留默认值

const capabilityCards = computed(() => {
  const list = infoConfig.value?.home?.capability_cards
  if (!Array.isArray(list) || !list.length) return defaultCapabilityCards
  return list
    .map((item) => {
      const title = (item?.title || '').trim()
      const description = (item?.description || '').trim()
      const icon = normalizeAssetUrl(item?.icon || '')
      const icon2x = normalizeAssetUrl(item?.icon_2x || '')
      const iconSrcset = icon2x ? `${icon} 1x, ${icon2x} 2x` : ''
      return { title, description, icon, iconSrcset }
    })
    .filter((item) => item.title && (item.description || item.icon))
})

const cssVars = computed(() => ({
  '--home-primary': theme.value.primary,
  '--home-primary-hover': theme.value.primaryHover,
  '--home-hero-bg': themeStore.isDark ? 'var(--main-40)' : theme.value.heroBg,
  '--home-hero-bg-2': themeStore.isDark ? 'var(--main-20)' : 'var(--main-10)'
}))

const checkHealth = async () => {
  try {
    const response = await healthApi.checkHealth()
    if (response.status !== 'ok') {
      throw new Error('服务不可用')
    }
  } catch (e) {
    error.value = {
      title: '服务连接失败',
      message: '后端服务无法响应，请检查服务是否正常运行'
    }
    throw e
  }
}

const loadData = async () => {
  isLoading.value = true
  error.value = null

  try {
    await checkHealth()
    const data = await infoStore.loadInfoConfig(true)
    infoConfig.value = data || infoStore.infoConfig
  } catch (e) {
    console.error('加载失败:', e)
  } finally {
    isLoading.value = false
  }
}

const retryLoad = () => {
  loadData()
}

const goHome = () => {
  router.push('/')
}

const goLogin = () => {
  router.push('/login')
}

const goToChat = async () => {
  if (!userStore.isLoggedIn) {
    sessionStorage.setItem('redirect', '/agent')
    router.push('/login')
    return
  }

  try {
    await agentStore.initialize()
    router.push('/agent')
  } catch (error) {
    console.error('跳转到智能体页面失败:', error)
    router.push('/agent')
  }
}

onMounted(() => {
  loadData()
})
</script>

<style lang="less" scoped>
.home {
  --home-primary: #1d5eff;
  --home-primary-hover: #1a52e6;
  --home-hero-bg: #eaf3ff;
  --home-hero-bg-2: #f4fbff;
  --home-content-width: 1440px;
  --home-page-pad: clamp(24px, 5vw, 72px);
  --home-topbar-h: 76px;

  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  color: var(--color-text);
  background: var(--color-bg-container);
}

.state {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.state-text {
  color: var(--color-text-secondary);
  font-size: 14px;
  margin: 0;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--color-bg-container);
  border-bottom: 1px solid var(--gray-150);
}

.topbar-inner {
  width: min(calc(100% - var(--home-page-pad) * 2), var(--home-content-width));
  height: var(--home-topbar-h);
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  box-sizing: border-box;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: inherit;
  min-height: 40px;
  outline: none;
}

.brand-logo {
  height: 26px;
  width: auto;
  object-fit: contain;
}

.brand-text {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-org {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.2px;
}

.brand-name {
  font-size: 17px;
  font-weight: 600;
  opacity: 0.92;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.topbar-login {
  min-height: 40px;
  padding: 0 16px;
  border-radius: 8px;
  border: 1px solid var(--home-primary);
  background: var(--home-primary);
  color: #ffffff;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease;
  outline: none;

  &:hover {
    background: var(--home-primary-hover);
  }
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.hero {
  background:
    radial-gradient(
      circle at 16% 20%,
      color-mix(in srgb, var(--home-primary) 10%, transparent),
      transparent 46%
    ),
    linear-gradient(90deg, var(--home-hero-bg), var(--home-hero-bg-2));
  flex: none;
}

.hero-inner {
  width: min(calc(100% - var(--home-page-pad) * 2), var(--home-content-width));
  min-height: clamp(460px, 42vh, 540px);
  margin: 0 auto;
  padding: 36px 0;
  display: grid;
  grid-template-columns: minmax(360px, 0.82fr) minmax(520px, 1.18fr);
  align-items: center;
  gap: clamp(48px, 6vw, 96px);
  box-sizing: border-box;
}

.hero-left {
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-width: 0;
}

.hero-eyebrow {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--color-text-secondary);
}

.hero-title {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-weight: 700;
  line-height: 1.15;
}

.hero-title-main {
  font-size: clamp(40px, 3.1vw, 48px);
  color: var(--color-text);
}

.hero-title-accent {
  font-size: clamp(40px, 3.1vw, 48px);
  color: var(--home-primary);
}

.hero-description {
  margin: 0;
  font-size: 15px;
  line-height: 1.7;
  color: var(--color-text-secondary);
  max-width: 480px;
}

.hero-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-top: 4px;
}

.cta {
  min-height: 44px;
  padding: 0 20px;
  border-radius: 8px;
  background: var(--home-primary);
  color: #ffffff;
  font-weight: 700;
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  outline: none;
  transition: background 0.15s ease;

  &:hover {
    background: var(--home-primary-hover);
  }
}

.cta-arrow {
  font-weight: 900;
}

.hero-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  min-width: 0;
}

.hero-frame {
  width: min(100%, 680px);
  border-radius: 8px;
  border: 1px solid var(--gray-150);
  background: var(--gray-0);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.hero-frame-bar {
  height: 32px;
  background: var(--gray-25);
  border-bottom: 1px solid var(--gray-150);
  position: relative;

  &::before {
    content: '';
    position: absolute;
    left: 14px;
    top: 50%;
    width: 44px;
    height: 10px;
    transform: translateY(-50%);
    background:
      radial-gradient(circle at 5px 5px, #ff5f57 0 4px, transparent 4px),
      radial-gradient(circle at 22px 5px, #febc2e 0 4px, transparent 4px),
      radial-gradient(circle at 39px 5px, #28c840 0 4px, transparent 4px);
  }
}

.hero-image {
  width: 100%;
  height: auto;
  display: block;
}

.capabilities {
  background: var(--gray-25);
  flex: 1 1 auto;
  display: flex;
  align-items: flex-start;
  padding: clamp(40px, 4.4vh, 64px) 0 clamp(36px, 4.4vh, 56px);
  border-top: 1px solid var(--gray-150);
}

.cap-grid {
  width: min(calc(100% - var(--home-page-pad) * 2), var(--home-content-width));
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 20px;
}

.cap-card {
  background: var(--gray-0);
  border-radius: 8px;
  border: 1px solid var(--gray-150);
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cap-icon {
  width: 36px;
  height: 36px;
  object-fit: contain;
}

.cap-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
}

.cap-desc {
  margin: 0;
  font-size: 13px;
  line-height: 1.65;
  color: var(--color-text-secondary);
}

.footer {
  margin-top: auto;
  background: #0b1a37;
  min-height: 48px;
  padding: 12px var(--home-page-pad);
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
}

.footer-text {
  margin: 0;
  text-align: center;
  color: rgba(255, 255, 255, 0.75);
  font-size: 12px;
  letter-spacing: 0.2px;
}

.brand:focus-visible,
.topbar-login:focus-visible,
.cta:focus-visible {
  outline: 3px solid rgba(29, 94, 255, 0.35);
  outline-offset: 3px;
}

@media (min-width: 1200px) {
  .hero-title-accent {
    white-space: nowrap;
  }

  .cap-card {
    min-height: 152px;
  }
}

@media (min-width: 1200px) and (max-height: 1100px) {
  .hero-inner {
    min-height: clamp(420px, 38vh, 500px);
    padding: 28px 0;
  }

  .capabilities {
    padding: 32px 0 36px;
  }

  .cap-card {
    min-height: 144px;
    padding: 20px;
  }

  .footer {
    min-height: 44px;
    padding: 10px var(--home-page-pad);
  }
}

@media (min-width: 768px) and (max-width: 1199px) {
  .home {
    --home-page-pad: clamp(32px, 5vw, 56px);
  }

  .hero-inner {
    min-height: 420px;
    padding: 36px 0;
    grid-template-columns: minmax(280px, 0.8fr) minmax(400px, 1.2fr);
    gap: 32px;
  }

  .cap-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 768px) and (max-width: 1023px) {
  .hero-inner {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .hero-left {
    max-width: 560px;
  }
}

@media (max-width: 767px) {
  .home {
    --home-page-pad: 16px;
    --home-topbar-h: 60px;
  }

  .brand {
    min-width: 0;
  }

  .brand-logo {
    height: 20px;
    max-width: 128px;
  }

  .brand-name {
    display: none;
  }

  .hero-inner {
    grid-template-columns: 1fr;
    min-height: auto;
    padding: 36px 0;
    gap: 32px;
  }

  .hero-left {
    gap: 20px;
  }

  .hero-title-main,
  .hero-title-accent {
    font-size: clamp(32px, 10vw, 40px);
  }

  .hero-description {
    max-width: 100%;
  }

  .hero-right {
    justify-content: center;
  }

  .capabilities {
    padding: 40px 0;
  }

  .cap-grid {
    grid-template-columns: 1fr;
  }

  .cap-card {
    padding: 20px;
  }
}
</style>
