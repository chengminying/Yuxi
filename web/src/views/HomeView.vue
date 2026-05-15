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

<script setup lang="ts">
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
const error = ref<{ title: string; message: string } | null>(null)

type InfoConfig = {
  organization?: { name?: string; logo?: string }
  branding?: { name?: string; title?: string; subtitle?: string; subtitles?: string[] }
  footer?: { copyright?: string }
  theme?: {
    primary?: string
    primary_hover?: string
    hero_bg?: string
  }
  home?: {
    hero_image?: string
    hero_eyebrow?: string
    hero_description?: string
    capability_cards?: Array<{ title?: string; description?: string; icon?: string; icon_2x?: string }>
  }
}

const infoConfig = ref<InfoConfig | null>(null)

const normalizeAssetUrl = (url: string) => {
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
  return (text || '© 2025 All rights reserved').trim()
})

type CapabilityCard = {
  title: string
  description: string
  icon: string
  iconSrcset: string
}

const defaultCapabilityCards: CapabilityCard[] = [
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

const capabilityCards = computed<CapabilityCard[]>(() => {
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

const cssVars = computed<Record<string, string>>(() => ({
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
    infoConfig.value = (data || infoStore.infoConfig) as InfoConfig
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
  // 检查用户是否登录
  if (!userStore.isLoggedIn) {
    // 登录后应该跳转到默认智能体而不是/agent
    sessionStorage.setItem('redirect', '/') // 设置为首页，登录后会通过路由守卫处理重定向
    router.push('/login')
    return
  }

  // 根据用户角色进行跳转
  if (userStore.isAdmin) {
    // 管理员用户跳转到聊天页面
    await agentStore.initialize()
    router.push('/agent')
    return
  }

  // 普通用户跳转到默认智能体
  try {
    // 获取默认智能体
    const defaultAgent = agentStore.defaultAgent
    if (defaultAgent?.id) {
      router.push(`/agent/${defaultAgent.id}`)
    } else {
      router.push('/agent')
    }
  } catch (error) {
    console.error('跳转到智能体页面失败:', error)
    router.push('/')
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
  --home-topbar-h: 60px;
  --home-footer-h: 52px;
  --home-page-pad: 120px;
  --home-hero-h: clamp(320px, 50vh, 540px);

  min-height: 100vh;
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
  border-bottom: 1px solid color-mix(in srgb, var(--home-primary) 14%, transparent);
}

.topbar-inner {
  width: 100%;
  padding: 14px var(--home-page-pad);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  height: var(--home-topbar-h);
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
  height: 24px;
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
  font-size: 16px;
  font-weight: 600;
  opacity: 0.92;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.topbar-login {
  height: 32px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid rgba(29, 94, 255, 0.18);
  background: var(--home-primary);
  color: #ffffff;
  font-weight: 600;
  cursor: pointer;
  transition:
    background 0.15s ease,
    transform 0.15s ease;
  outline: none;

  &:hover {
    background: var(--home-primary-hover);
  }

  &:active {
    transform: translateY(1px);
  }
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.hero {
  background:
    radial-gradient(circle at 18% 28%, rgba(29, 94, 255, 0.12), transparent 55%),
    radial-gradient(circle at 82% 18%, rgba(29, 94, 255, 0.1), transparent 50%),
    linear-gradient(90deg, var(--home-hero-bg), var(--home-hero-bg-2));
  flex: none;
  height: var(--home-hero-h);
}

.hero-inner {
  width: 100%;
  padding: clamp(14px, 2.2vh, 26px) var(--home-page-pad) clamp(12px, 2vh, 20px);
  display: flex;
  justify-content: space-around;
  align-items: center;
  gap: 44px;
  height: 100%;
  box-sizing: border-box;
}

.hero-left {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.hero-eyebrow {
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--color-text-secondary);
}

.hero-title {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-weight: 900;
  line-height: 1.12;
}

.hero-title-main {
  font-size: clamp(40px, 4.2vw, 56px);
  color: var(--color-text);
}

.hero-title-accent {
  font-size: clamp(40px, 4.2vw, 56px);
  color: var(--home-primary);
}

.hero-description {
  margin: 0;
  font-size: 14px;
  line-height: 1.75;
  color: var(--color-text-secondary);
  max-width: 520px;
}

.hero-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-top: 8px;
}

.cta {
  height: 40px;
  padding: 0 16px;
  border-radius: 10px;
  background: var(--home-primary);
  color: #ffffff;
  font-weight: 700;
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 10px 22px color-mix(in srgb, var(--home-primary) 28%, transparent);
  outline: none;
  transition:
    background 0.15s ease,
    transform 0.15s ease,
    box-shadow 0.15s ease;

  &:hover {
    background: var(--home-primary-hover);
    box-shadow: 0 14px 28px color-mix(in srgb, var(--home-primary) 30%, transparent);
  }

  &:active {
    transform: translateY(1px);
  }
}

.cta-arrow {
  font-weight: 900;
}

.hero-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  align-self: stretch;
  min-width: 0;
}

.hero-frame {
  width: min(980px, 100%);
  height: 100%;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--home-primary) 18%, transparent);
  background: color-mix(in srgb, var(--color-bg-container) 92%, transparent);
  box-shadow: 0 18px 48px var(--shadow-2);
  overflow: hidden;
  max-height: 100%;
  display: flex;
  flex-direction: column;
}

.hero-frame-bar {
  height: 34px;
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--color-bg-container) 92%, transparent),
    color-mix(in srgb, var(--color-bg-container) 76%, transparent)
  );
  border-bottom: 1px solid color-mix(in srgb, var(--home-primary) 14%, transparent);
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
  height: 100%;
  display: block;
  flex: 1 1 auto;
  min-height: 0;
  object-fit: contain;
}

.capabilities {
  background: var(--color-bg-container);
  flex: 1 1 auto;
}

.cap-grid {
  // margin-top: 5%;
  width: 100%;
  height: 100%;
  padding: clamp(10px, 1.6vh, 16px) var(--home-page-pad) clamp(12px, 1.9vh, 18px);
  --cap-cols: 4;
  --cap-gap: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: var(--cap-gap);
  box-sizing: border-box;
}

.cap-card {
  flex: 0 0 calc((100% - (var(--cap-cols) - 1) * var(--cap-gap)) / var(--cap-cols));
  background: var(--color-bg-elevated);
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--home-primary) 14%, transparent);
  box-shadow: 0 10px 22px var(--shadow-2);
  padding: 14px 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 9px;
  min-height: 0;
}

.cap-icon {
  width: 34px;
  height: 34px;
  object-fit: contain;
}

.cap-title {
  margin: 0;
  font-size: 14px;
  font-weight: 800;
  color: var(--color-text);
}

.cap-desc {
  margin: 0;
  font-size: 12px;
  line-height: 1.6;
  color: var(--color-text-secondary);
}

.footer {
  margin-top: auto;
  background: #0b1a37;
  padding: 18px 20px 22px;
  height: var(--home-footer-h);
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
  .hero-inner {
    padding-top: clamp(18px, 3.6vh, 34px);
  }
}

@media (min-width: 768px) and (max-width: 1199px) {
  .home {
    --home-page-pad: 56px;
    --home-hero-h: clamp(300px, 46vh, 520px);
  }

  .hero-inner {
    grid-template-columns: 1fr;
    justify-items: center;
    text-align: center;
    padding: clamp(16px, 3vh, 28px) var(--home-page-pad) clamp(12px, 2.6vh, 22px);
    gap: 28px;
    min-height: auto;
  }

  .hero-right {
    justify-content: center;
  }

  .hero-description {
    margin: 0 auto;
  }

  .cap-grid {
    --cap-cols: 2;
  }
}

@media (max-width: 767px) {
  .home {
    --home-page-pad: 16px;
    --home-hero-h: clamp(260px, 44vh, 460px);
  }

  .topbar-inner {
    padding: 12px var(--home-page-pad);
  }

  .brand-logo {
    height: 20px;
  }

  .brand-org,
  .brand-name {
    font-size: 14px;
  }

  .hero-inner {
    grid-template-columns: 1fr;
    padding: clamp(14px, 2.8vh, 22px) var(--home-page-pad) clamp(10px, 2.2vh, 18px);
    gap: 18px;
    min-height: auto;
  }

  .hero-title-main,
  .hero-title-accent {
    font-size: 34px;
  }

  .hero-description {
    max-width: 100%;
  }

  .hero-right {
    justify-content: center;
  }

  .cap-grid {
    --cap-cols: 1;
    padding: 12px var(--home-page-pad);
  }
}
</style>
