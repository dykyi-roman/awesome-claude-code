.PHONY: help list-commands list-skills list-agents validate-claude validate-strict \
        token-budget eval eval-smoke test changelog release

.DEFAULT_GOAL := help

# Colors
GREEN  := \033[0;32m
YELLOW := \033[0;33m
CYAN   := \033[0;36m
RESET  := \033[0m

help: ## Show this help
	@echo ""
	@echo "$(CYAN)Available commands:$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# =============================================================================
# Claude Components
# =============================================================================

list-commands: ## List all available slash commands
	@echo ""
	@echo "$(CYAN)Available Commands:$(RESET)"
	@echo ""
	@if [ -d "commands" ]; then \
		find commands -name "*.md" -type f | while read file; do \
			name=$$(basename "$$file" .md); \
			desc=$$(head -1 "$$file" 2>/dev/null | sed 's/^#* *//'); \
			printf "  $(GREEN)/acc:%-20s$(RESET) %s\n" "$$name" "$$desc"; \
		done; \
	else \
		echo "  $(YELLOW)No commands found$(RESET)"; \
	fi
	@echo ""

list-skills: ## List all available skills
	@echo ""
	@echo "$(CYAN)Available Skills:$(RESET)"
	@echo ""
	@if [ -d "skills" ]; then \
		find skills -name "SKILL.md" -type f | while read file; do \
			name=$$(echo "$$file" | sed 's|skills/||;s|/SKILL.md||'); \
			desc=$$(grep -m1 "^description:" "$$file" 2>/dev/null | sed 's/^description: *//'); \
			printf "  $(GREEN)%-40s$(RESET) %s\n" "$$name" "$$desc"; \
		done; \
	else \
		echo "  $(YELLOW)No skills found$(RESET)"; \
	fi
	@echo ""

list-agents: ## List all available agents
	@echo ""
	@echo "$(CYAN)Available Agents:$(RESET)"
	@echo ""
	@if [ -d "agents" ]; then \
		find agents -name "*.md" -type f | while read file; do \
			name=$$(basename "$$file" .md); \
			desc=$$(head -1 "$$file" 2>/dev/null | sed 's/^#* *//'); \
			printf "  $(GREEN)%-30s$(RESET) %s\n" "$$name" "$$desc"; \
		done; \
	else \
		echo "  $(YELLOW)No agents found$(RESET)"; \
	fi
	@echo ""

validate-claude: ## Validate plugin structure and content (real gate)
	@echo ""
	@echo "$(CYAN)Structural + regression validation$(RESET)"
	@python3 scripts/validate.py
	@echo "$(CYAN)Official CLI validation$(RESET)"
	@for t in . skills agents commands; do \
		printf "  %-10s " "$$t"; \
		claude plugin validate "$$t" --strict 2>&1 | tail -1; \
	done
	@echo ""
	@echo "  $(YELLOW)note:$(RESET) .claude-plugin/plugin.json is validated without --strict on purpose —"
	@echo "  it warns that the root CLAUDE.md is not shipped to users, which is intended here."
	@claude plugin validate .claude-plugin/plugin.json 2>&1 | tail -1
	@echo ""

validate-strict: ## Validate and fail on warnings too (grep-pattern debt included)
	@python3 scripts/validate.py --strict

token-budget: ## Show the always-on context cost the plugin adds to every session
	@echo ""
	@claude plugin details acc 2>/dev/null | grep -E "Always-on|Component inventory" || \
		echo "  $(YELLOW)plugin 'acc' is not installed — run /plugin install acc@awesome-claude-code$(RESET)"
	@echo ""

eval-smoke: ## Fast behavioural check for PRs (subset, 1 run per case)
	@claude plugin eval . --tag smoke --runs 1 --threshold 0.8

eval: ## Full behavioural regression suite
	@claude plugin eval . --runs 3 --json evals/results/latest.json

test: validate-claude ## Alias: run every check that works offline

# =============================================================================
# Release
# =============================================================================

changelog: ## Generate changelog from git commits
	@echo ""
	@echo "$(CYAN)Changelog:$(RESET)"
	@echo ""
	@git log --oneline --no-merges HEAD~10..HEAD 2>/dev/null || git log --oneline --no-merges -10
	@echo ""

release: validate-claude ## Prepare release (run checks)
	@echo ""
	@echo "$(GREEN)All checks passed!$(RESET)"
	@echo ""
	@echo "$(CYAN)To create a release:$(RESET)"
	@echo "  1. git add -A && git commit -m 'Release vX.Y.Z'"
	@echo "  2. git tag vX.Y.Z"
	@echo "  3. git push origin master --tags"
	@echo ""
