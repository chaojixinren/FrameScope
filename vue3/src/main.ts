import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import { useUserStore } from './stores/user'
import './style.css'
import './styles/theme.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// 应用启动时初始化认证状态
const userStore = useUserStore()
userStore.initAuth()

app.mount('#app')
