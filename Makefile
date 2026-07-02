# Dagger pipeline shortcuts.
# Wraps the two env vars the local setup needs:
#   PATH        — hides the stopped docker binary so Dagger uses Apple `container`
#   DOCKER_CONFIG — empty config, dodges the leftover Docker Desktop credsStore
DAGGER := PATH="$(HOME)/.local/bin:/opt/homebrew/bin:/usr/bin:/bin" \
          DOCKER_CONFIG="$(HOME)/.local/dagger-dockercfg" \
          dagger call

.PHONY: test lint build ci
test:
	$(DAGGER) test
lint:
	$(DAGGER) lint
build:
	$(DAGGER) build
ci:
	$(DAGGER) ci
