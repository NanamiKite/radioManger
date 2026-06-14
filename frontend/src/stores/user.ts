import { defineStore } from "pinia"
import router from "@/router"

export const useUserStore = defineStore("user", {
  state: () => ({
    token: localStorage.getItem("token") || "",
    user: null as any
  }),

  getters: {
    isLogin: (state) => !!state.token
  },

  actions: {
    setToken(token: string) {
      this.token = token
      localStorage.setItem("token", token)
    },

    setUser(user: any) {
      this.user = user
    },

    logout() {
      this.token = ""
      this.user = null
      localStorage.removeItem("token")

      router.push("/login") 
    }
  }
})