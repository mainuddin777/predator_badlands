"""
Honour and Reputation System

"""


class HonourSystem:
    """
    Manage honour/reputation for Predators
    Based on Yautja Clan Code principles
    """

    # Honour thresholds for rank progression
    RANKS = {
        'Unblooded': 0,
        'Blooded': 30,
        'Honoured': 60,
        'Elite': 100,
        'Ancient': 150
    }

    # Honour modifiers for different actions
    HONOUR_VALUES = {
        'hunt_worthy_prey': 15,
        'hunt_unworthy_prey': -30,
        'defeat_adversary': 100,
        'successful_challenge': 10,
        'failed_challenge': -5,
        'retreat_from_combat': -10,
        'help_wounded': 5,
        'trophy_collected': 10,
        'dishonourable_kill': -50,
        'win_clan_challenge': 15,
        'lose_clan_challenge': -5,
        'spare_worthy_opponent': 20,
        'fight_alongside_ally': 5
    }

    @staticmethod
    def update_honour(predator, action: str, context: dict = None) -> int:
        """
        Update predator's honour based on action
        """
        if not hasattr(predator, 'honour'):
            return 0

        honour_change = HonourSystem.HONOUR_VALUES.get(action, 0)

        # Apply context-based modifications
        if context:
            honour_change = HonourSystem._apply_context(honour_change, action, context)

        old_honour = predator.honour
        predator.honour += honour_change
        predator.honour = max(0, predator.honour)

        # Check for rank change
        old_rank = HonourSystem.get_rank(old_honour)
        new_rank = HonourSystem.get_rank(predator.honour)

        if new_rank != old_rank:
            HonourSystem._announce_rank_change(predator, old_rank, new_rank)

        # Log honour change
        if honour_change != 0:
            sign = "+" if honour_change > 0 else ""
            print(f"🏅 {predator.name} honour: {sign}{honour_change} "
                  f"(Total: {predator.honour}) [{new_rank}]")

        return honour_change

    @staticmethod
    def _apply_context(base_honour: int, action: str, context: dict) -> int:

        honour = base_honour

        # Check if prey was worthy according to Yautja code
        if action == 'hunt_worthy_prey' and context.get('target'):
            target = context['target']

            # Wildlife is ALWAYS worthy if threat_level >= 1
            if target.__class__.__name__ == 'Wildlife':
                if hasattr(target, 'threat_level') and target.threat_level >= 1:
                    # Worthy prey - positive honour
                    return 15 + (target.threat_level * 5)  # Bonus for higher threat
                else:
                    # No threat level or 0 threat
                    return -30  # Dishonourable

            # For Adversary - always worthy
            elif target.__class__.__name__ in ['Adversary', 'AdaptiveAdversary']:
                return 100  # Massive honour for adversary

            # Default for other agents
            return 15

        # Combat context
        if action in ['retreat_from_combat']:
            # Less penalty if health is critical
            if context.get('health', 100) < 20:
                honour = int(honour * 0.5)

        # Challenge context
        if action in ['successful_challenge', 'failed_challenge']:
            opponent_honour = context.get('opponent_honour', 50)
            if opponent_honour > 70:
                honour = int(honour * 1.5)

        return honour

    @staticmethod
    def get_rank(honour: int) -> str:
        """Get rank title based on honour"""
        for rank in reversed(list(HonourSystem.RANKS.keys())):
            if honour >= HonourSystem.RANKS[rank]:
                return rank
        return 'Unblooded'

    @staticmethod
    def _announce_rank_change(predator, old_rank: str, new_rank: str):
        """Announce rank progression or demotion"""
        if HonourSystem.RANKS[new_rank] > HonourSystem.RANKS[old_rank]:
            print(f"\n🎖️  RANK UP! {predator.name} is now {new_rank}!")
        else:
            print(f"\n📉 RANK DOWN! {predator.name} demoted to {new_rank}")

    @staticmethod
    def check_clan_acceptance(predator, clan_honour_requirement: int = 50) -> bool:
        """Check if predator has enough honour for clan acceptance"""
        return predator.honour >= clan_honour_requirement

    @staticmethod
    def validate_hunt(predator, target) -> dict:
        """
        Validate if hunting this target is honourable
        """
        violations = []
        is_honourable = True

        # Wildlife is worthy if threat_level >= 1
        if target.__class__.__name__ == 'Wildlife':
            if hasattr(target, 'threat_level'):
                if target.threat_level >= 1:
                    # This IS worthy prey
                    is_honourable = True
                else:
                    violations.append("Wildlife has no threat level - unworthy")
                    is_honourable = False
            else:
                violations.append("Wildlife cannot defend itself")
                is_honourable = False

        # Adversary is always worthy
        elif target.__class__.__name__ in ['Adversary', 'AdaptiveAdversary']:
            is_honourable = True

        # Check if target is too wounded
        if hasattr(target, 'health') and hasattr(target, 'max_health'):
            if target.health < target.max_health * 0.2:
                violations.append("Target is too wounded - dishonourable")
                is_honourable = False

        return {
            'honourable': is_honourable,
            'violations': violations,
            'recommended_action': 'hunt' if is_honourable else 'spare'
        }

    @staticmethod
    def get_honour_summary(predator) -> dict:
        """Get complete honour status summary"""
        rank = HonourSystem.get_rank(predator.honour)
        next_rank_threshold = None

        # Find next rank
        for r, threshold in HonourSystem.RANKS.items():
            if threshold > predator.honour:
                next_rank_threshold = threshold
                break

        progress_to_next = None
        needed = 0
        if next_rank_threshold:
            progress_to_next = predator.honour - HonourSystem.RANKS[rank]
            needed = next_rank_threshold - predator.honour

        return {
            'current_honour': predator.honour,
            'rank': rank,
            'next_rank_threshold': next_rank_threshold,
            'honour_needed': needed,
            'clan_acceptance': HonourSystem.check_clan_acceptance(predator)
        }