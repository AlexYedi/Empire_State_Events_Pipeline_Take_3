import type { RepoInfo } from '../server/utils'

interface ReposResponse {
  count: number
  repositories: RepoInfo[]
}

export function useGitHub() {
  const fetchRepos = (options: { force?: boolean, lazy?: boolean, owner?: string } = {}) => {
    return useFetch<ReposResponse>('/api/github/repos', {
      query: { force: options.force, owner: options.owner },
      lazy: options.lazy,
    })
  }

  return { fetchRepos }
}
