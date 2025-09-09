.PHONY: help lint lint-backend lint-frontend

help: ## Show this help message
	@echo "Puntini Project Development Commands"
	@echo "===================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Run backend linters
	@echo "--- Running backend linters ---"
	$(MAKE) -C apps/backend lint

lint-frontend: ## Run frontend linters
	@echo "--- Running frontend linters ---"
	cd apps/frontend && npm run lint

lint-frontend-fix: ## Run frontend linters and fix issues
	@echo "--- Running frontend linters and fixing issues ---"
	cd apps/frontend && npm run lint:fix
