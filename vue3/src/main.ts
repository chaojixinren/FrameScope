import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import { useUserStore } from './stores/user'
import { useThemeStore } from './stores/theme'
import './style.css'
import './styles/theme.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// 应用启动时初始化主题（在所有页面加载前）
const themeStore = useThemeStore()
themeStore.initTheme()
themeStore.watchSystemTheme()

// 应用启动时初始化认证状态
const userStore = useUserStore()
userStore.initAuth()

app.mount('#app')
