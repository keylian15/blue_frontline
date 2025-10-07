from Class.units.Bateau import Bateau
class IA_bateaux(Bateau):
    engage = ["bateau", "challoupe", "eclaireur", "sous_marin"]
    avoid = ["paquebot"]

    def __init__(self, game, team):
        super().__init__(game, team)
        self.current_goal = None
        self.engage_radius = 300.0
        self.avoid_radius = 220.0

    def update(self, dt: int = 0, combat_system=None, screen=None, camera_offset=(0, 0), all_units=None):
        super().update(dt, combat_system, screen, camera_offset, all_units)
        print("goal:", self.current_goal, "is_moving:", self.is_moving, "pos:", self.position)
        if self.current_goal is None:
            self.find_goal()
        else:
            self.move_towards_goal()

    def find_goal(self):
        base_enemie = self.get_base()
        if base_enemie:
            self.current_goal = tuple(base_enemie.position)
        else:
            self.current_goal = None

    def move_towards_goal(self):
        if self.current_goal:
            self.move_to_position(self.current_goal)
    
    def get_base(self):
        # Renvoie la base ennemie
        for p in self.game.plateformes:
            if p.team != self.team:
                return p
        return None


