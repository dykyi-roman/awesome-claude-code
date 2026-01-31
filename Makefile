.PHONY: help list-commands list-skills list-agents validate-claude changelog release

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
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# =============================================================================
# Claude Components
# =============================================================================

list-commands: ## List all available slash commands
	@echo ""
	@echo "$(CYAN)Available Commands:$(RESET)"
	@echo ""
	@if [ -d ".claude/commands" ]; then \
		find .claude/commands -name "*.md" -type f | while read file; do \
			name=$$(basename "$$file" .md); \
			desc=$$(head -1 "$$file" 2>/dev/null | sed 's/^#* *//'); \
			printf "  $(GREEN)/%-20s$(RESET) %s\n" "$$name" "$$desc"; \
		done; \
	else \
		echo "  $(YELLOW)No commands found$(RESET)"; \
	fi
	@echo ""

list-skills: ## List all available skills
	@echo ""
	@echo "$(CYAN)Available Skills:$(RESET)"
	@echo ""
	@if [ -d ".claude/skills" ]; then \
		find .claude/skills -name "*.md" -type f | while read file; do \
			name=$$(basename "$$file" .md); \
			desc=$$(grep -m1 "^description:" "$$file" 2>/dev/null | sed 's/^description: *//'); \
			printf "  $(GREEN)%-20s$(RESET) %s\n" "$$name" "$$desc"; \
		done; \
	else \
		echo "  $(YELLOW)No skills found$(RESET)"; \
	fi
	@echo ""

list-agents: ## List all available agents
	@echo ""
	@echo "$(CYAN)Available Agents:$(RESET)"
	@echo ""
	@if [ -d ".claude/agents" ]; then \
		find .claude/agents -name "*.md" -type f | while read file; do \
			name=$$(basename "$$file" .md); \
			desc=$$(head -1 "$$file" 2>/dev/null | sed 's/^#* *//'); \
			printf "  $(GREEN)%-20s$(RESET) %s\n" "$$name" "$$desc"; \
		done; \
	else \
		echo "  $(YELLOW)No agents found$(RESET)"; \
	fi
	@echo ""

validate-claude: ## Validate .claude directory structure
	@echo ""
	@echo "$(CYAN)Validating .claude structure...$(RESET)"
	@echo ""
	@errors=0; \
	if [ ! -d ".claude" ]; then \
		echo "  $(YELLOW)Warning: .claude directory not found$(RESET)"; \
		exit 0; \
	fi; \
	for dir in commands skills agents; do \
		if [ -d ".claude/$$dir" ]; then \
			echo "  $(GREEN)✓$(RESET) .claude/$$dir exists"; \
			count=$$(find ".claude/$$dir" -name "*.md" -type f | wc -l | tr -d ' '); \
			echo "    Found $$count markdown files"; \
		else \
			echo "  $(YELLOW)○$(RESET) .claude/$$dir not found (optional)"; \
		fi; \
	done; \
	echo ""; \
	echo "$(CYAN)Checking markdown syntax...$(RESET)"; \
	find .claude -name "*.md" -type f | while read file; do \
		if head -1 "$$file" | grep -q "^#\|^---"; then \
			echo "  $(GREEN)✓$(RESET) $$file"; \
		else \
			echo "  $(YELLOW)?$(RESET) $$file (no header found)"; \
		fi; \
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
	@echo "  1. Update version in composer.json (if needed)"
	@echo "  2. git add -A && git commit -m 'Release vX.Y.Z'"
	@echo "  3. git tag vX.Y.Z"
	@echo "  4. git push origin master --tags"
	@echo ""
