import { useI18n } from 'vue-i18n'

export function useAgentI18n() {
  const { t } = useI18n()

  const getAgentDisplayName = (agentName: string): string => {
    const key = `agents.names.${agentName}`
    const translated = t(key)
    return translated === key ? agentName : translated
  }

  const getAgentDescription = (agentName: string): string => {
    const key = `agents.descriptions.${agentName}`
    const translated = t(key)
    return translated === key ? '' : translated
  }

  return { getAgentDisplayName, getAgentDescription }
}
