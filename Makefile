.PHONY: help list-commands list-skills list-agents validate-claude validate-plugin changelog release

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

validate-claude: ## Validate plugin structure
	@echo ""
	@echo "$(CYAN)Validating plugin structure...$(RESET)"
	@echo ""
	@if [ ! -d ".claude-plugin" ]; then \
		echo "  $(YELLOW)Warning: .claude-plugin directory not found$(RESET)"; \
		exit 1; \
	fi; \
	echo "  $(GREEN)✓$(RESET) .claude-plugin/ exists"; \
	for file in marketplace.json plugin.json; do \
		if [ -f ".claude-plugin/$$file" ]; then \
			echo "  $(GREEN)✓$(RESET) .claude-plugin/$$file"; \
		else \
			echo "  $(YELLOW)✗$(RESET) .claude-plugin/$$file missing"; \
		fi; \
	done; \
	for dir in commands skills agents; do \
		if [ -d "$$dir" ]; then \
			count=$$(find "$$dir" -name "*.md" -type f | wc -l | tr -d ' '); \
			echo "  $(GREEN)✓$(RESET) $$dir/ ($$count files)"; \
		else \
			echo "  $(YELLOW)○$(RESET) $$dir/ not found"; \
		fi; \
	done; \
	echo ""; \
	echo "$(CYAN)Checking markdown syntax...$(RESET)"; \
	for dir in commands agents; do \
		find $$dir -name "*.md" -type f | while read file; do \
			if head -1 "$$file" | grep -q "^#\|^---"; then \
				echo "  $(GREEN)✓$(RESET) $$file"; \
			else \
				echo "  $(YELLOW)?$(RESET) $$file (no header found)"; \
			fi; \
		done; \
	done; \
	echo ""

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
