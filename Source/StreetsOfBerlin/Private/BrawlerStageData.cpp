#include "BrawlerStageData.h"

namespace
{
	FSpawnGroup Group(std::initializer_list<const TCHAR*> Names, int32 WhenAlive = 0, float Delay = 12.f)
	{
		FSpawnGroup G;
		for (const TCHAR* N : Names)
		{
			G.Enemies.Add(FName(N));
		}
		G.WhenAliveAtMost = WhenAlive;
		G.MaxDelay = Delay;
		return G;
	}

	FEncounter Encounter(float Trigger, float Lock, TArray<FSpawnGroup> Groups, bool bBoss = false)
	{
		FEncounter E;
		E.TriggerX = Trigger;
		E.LockCenterX = Lock;
		E.Groups = MoveTemp(Groups);
		E.bBoss = bBoss;
		return E;
	}

	FStageArea Area(float Start, float End, std::initializer_list<const TCHAR*> Walls, const TCHAR* Floor, const TCHAR* Sky,
		const TCHAR* Fg, std::initializer_list<float> FgX)
	{
		FStageArea A;
		A.StartX = Start;
		A.EndX = End;
		for (const TCHAR* W : Walls)
		{
			A.Walls.Add(W);
		}
		A.Floor = Floor;
		A.Sky = Sky ? Sky : TEXT("");
		A.Foreground = Fg ? Fg : TEXT("");
		A.ForegroundX = FgX;
		return A;
	}

	FPropSpawn Prop(const TCHAR* Type, float X, float Depth, const TCHAR* Drop)
	{
		FPropSpawn P;
		P.Type = FName(Type);
		P.X = X;
		P.Depth = Depth;
		P.Drop = Drop ? FName(Drop) : NAME_None;
		return P;
	}

	FWeaponSpawn Weapon(const TCHAR* Type, float X, float Depth)
	{
		FWeaponSpawn W;
		W.Type = FName(Type);
		W.X = X;
		W.Depth = Depth;
		return W;
	}

	constexpr float BossLock = Brawler::StageEndX - Brawler::ScreenWidth * 0.5f;

	TArray<FStageDef> BuildStages()
	{
		TArray<FStageDef> Stages;

		// --- Stage 1: Kreuzberg bei Nacht -----------------------------------------
		{
			FStageDef S;
			S.Name = TEXT("STAGE 1");
			S.Title = TEXT("KREUZBERG BEI NACHT");
			S.Areas.Add(Area(0.f, 4096.f, { TEXT("BG_Street_00"), TEXT("BG_Street_01") }, TEXT("BG_FloorStreet"), TEXT("BG_Sky"),
				TEXT("FG_LampPost"), { 1500.f, 2900.f, 3800.f }));
			S.Areas.Add(Area(4096.f, 10240.f, { TEXT("BG_UBahn_00"), TEXT("BG_UBahn_00"), TEXT("BG_UBahn_00") }, TEXT("BG_FloorPlatform"),
				nullptr, TEXT("FG_Pillar"), { 4900.f, 6100.f, 7300.f }));
			S.Encounters.Add(Encounter(560.f, 900.f, { Group({ TEXT("Kalle"), TEXT("Kalle") }), Group({ TEXT("Ronny") }, 1, 10.f), Group({ TEXT("Kalle"), TEXT("Jojo") }, 1, 12.f) }));
			S.Encounters.Add(Encounter(1760.f, 2100.f, { Group({ TEXT("Jojo"), TEXT("Kalle"), TEXT("Ronny") }), Group({ TEXT("Deniz"), TEXT("Kalle") }, 1, 12.f) }));
			S.Encounters.Add(Encounter(2960.f, 3300.f, { Group({ TEXT("Brecher") }), Group({ TEXT("Ronny"), TEXT("Jojo") }, 1, 6.f), Group({ TEXT("Kalle"), TEXT("Deniz") }, 1, 12.f) }));
			S.Encounters.Add(Encounter(4560.f, 4900.f, { Group({ TEXT("Kalle"), TEXT("Ronny"), TEXT("Deniz") }), Group({ TEXT("Jojo"), TEXT("Jojo") }, 1, 10.f), Group({ TEXT("Brecher") }, 1, 14.f) }));
			S.Encounters.Add(Encounter(5860.f, 6200.f, { Group({ TEXT("Brecher"), TEXT("Kalle") }), Group({ TEXT("Deniz"), TEXT("Ronny"), TEXT("Jojo") }, 1, 10.f), Group({ TEXT("Brecher") }, 1, 14.f) }));
			S.Encounters.Add(Encounter(7050.f, BossLock, { Group({ TEXT("Rolf") }), Group({ TEXT("Kalle"), TEXT("Ronny") }, 1, 15.f), Group({ TEXT("Jojo"), TEXT("Deniz") }, 1, 22.f) }, true));
			S.Props = { Prop(TEXT("TrashCan"), 1050.f, 222.f, TEXT("Currywurst")), Prop(TEXT("Crate"), 1520.f, 205.f, TEXT("Money")),
				Prop(TEXT("TrashCan"), 2650.f, 225.f, TEXT("Doener")), Prop(TEXT("Crate"), 3560.f, 210.f, TEXT("Currywurst")),
				Prop(TEXT("TrashCan"), 4450.f, 225.f, TEXT("Money")), Prop(TEXT("Crate"), 5600.f, 200.f, TEXT("Doener")),
				Prop(TEXT("TrashCan"), 6700.f, 222.f, TEXT("Currywurst")), Prop(TEXT("Crate"), 6950.f, 90.f, TEXT("Doener")) };
			S.Weapons = { Weapon(TEXT("Pipe"), 1300.f, 60.f), Weapon(TEXT("Bottle"), 2500.f, 150.f), Weapon(TEXT("Pipe"), 5200.f, 120.f) };
			Stages.Add(S);
		}

		// --- Stage 2: East Side Gallery + Club-Hinterhof -----------------------------
		{
			FStageDef S;
			S.Name = TEXT("STAGE 2");
			S.Title = TEXT("EAST SIDE GALLERY");
			S.Areas.Add(Area(0.f, 4096.f, { TEXT("BG_Gallery_00"), TEXT("BG_Gallery_01") }, TEXT("BG_FloorPromenade"), TEXT("BG_SkySpree"),
				TEXT("FG_Tree"), { 1300.f, 2700.f, 3700.f }));
			S.Areas.Add(Area(4096.f, 10240.f, { TEXT("BG_Backyard_00"), TEXT("BG_Backyard_00"), TEXT("BG_Backyard_00") }, TEXT("BG_FloorCobble"),
				TEXT("BG_SkySpree"), TEXT("FG_Tree"), { 5400.f }));
			S.Encounters.Add(Encounter(560.f, 900.f, { Group({ TEXT("Zoe"), TEXT("Kalle") }), Group({ TEXT("Micha"), TEXT("Jojo") }, 1, 10.f) }));
			S.Encounters.Add(Encounter(1760.f, 2100.f, { Group({ TEXT("Nina"), TEXT("Ronny"), TEXT("Deniz") }), Group({ TEXT("Micha"), TEXT("Zoe") }, 1, 12.f) }));
			S.Encounters.Add(Encounter(2960.f, 3300.f, { Group({ TEXT("Brecher"), TEXT("Micha") }), Group({ TEXT("Zoe"), TEXT("Nina") }, 1, 8.f) }));
			S.Encounters.Add(Encounter(4560.f, 4900.f, { Group({ TEXT("Kalle"), TEXT("Micha"), TEXT("Deniz") }), Group({ TEXT("Brecher"), TEXT("Jojo") }, 1, 12.f) }));
			S.Encounters.Add(Encounter(5860.f, 6200.f, { Group({ TEXT("Nina"), TEXT("Zoe"), TEXT("Micha") }), Group({ TEXT("Ronny"), TEXT("Deniz"), TEXT("Kalle") }, 1, 12.f) }));
			S.Encounters.Add(Encounter(7050.f, BossLock, { Group({ TEXT("Sven") }), Group({ TEXT("Micha"), TEXT("Nina") }, 1, 16.f), Group({ TEXT("Zoe"), TEXT("Ronny") }, 1, 24.f) }, true));
			S.Props = { Prop(TEXT("Crate"), 1100.f, 220.f, TEXT("Currywurst")), Prop(TEXT("TrashCan"), 2300.f, 210.f, TEXT("Money")),
				Prop(TEXT("Crate"), 3600.f, 215.f, TEXT("Doener")), Prop(TEXT("TrashCan"), 4700.f, 225.f, TEXT("Currywurst")),
				Prop(TEXT("Crate"), 5500.f, 200.f, TEXT("Money")), Prop(TEXT("TrashCan"), 6800.f, 222.f, TEXT("Doener")) };
			S.Weapons = { Weapon(TEXT("Bat"), 1000.f, 80.f), Weapon(TEXT("Bottle"), 4400.f, 190.f), Weapon(TEXT("Bottle"), 6300.f, 60.f) };
			Stages.Add(S);
		}

		// --- Stage 3: Baustelle am Alex + Dach ------------------------------------
		{
			FStageDef S;
			S.Name = TEXT("STAGE 3");
			S.Title = TEXT("BAUSTELLE AM ALEX");
			S.Areas.Add(Area(0.f, 4096.f, { TEXT("BG_Construction_00"), TEXT("BG_Construction_01") }, TEXT("BG_FloorConstruction"),
				TEXT("BG_SkyAlex"), TEXT("FG_Scaffold"), { 1400.f, 2800.f, 3900.f }));
			S.Areas.Add(Area(4096.f, 10240.f, { TEXT("BG_Rooftop_00"), TEXT("BG_Rooftop_00"), TEXT("BG_Rooftop_00") }, TEXT("BG_FloorRooftop"),
				TEXT("BG_SkyRooftop"), nullptr, {}));
			S.Encounters.Add(Encounter(560.f, 900.f, { Group({ TEXT("Micha"), TEXT("Zoe"), TEXT("Kalle") }), Group({ TEXT("Deniz"), TEXT("Nina") }, 1, 10.f) }));
			S.Encounters.Add(Encounter(1760.f, 2100.f, { Group({ TEXT("Brecher"), TEXT("Nina") }), Group({ TEXT("Micha"), TEXT("Micha") }, 1, 10.f), Group({ TEXT("Jojo"), TEXT("Zoe") }, 1, 14.f) }));
			S.Encounters.Add(Encounter(2960.f, 3300.f, { Group({ TEXT("RolfII") }), Group({ TEXT("Ronny"), TEXT("Kalle") }, 1, 10.f) }));
			S.Encounters.Add(Encounter(4560.f, 4900.f, { Group({ TEXT("Zoe"), TEXT("Nina"), TEXT("Micha") }), Group({ TEXT("Brecher"), TEXT("Deniz") }, 1, 12.f) }));
			S.Encounters.Add(Encounter(5860.f, 6200.f, { Group({ TEXT("Brecher"), TEXT("Brecher") }), Group({ TEXT("Nina"), TEXT("Micha"), TEXT("Zoe") }, 1, 12.f) }));
			S.Encounters.Add(Encounter(7050.f, BossLock, { Group({ TEXT("Harald") }), Group({ TEXT("Micha"), TEXT("Nina") }, 0, 18.f) }, true));
			S.Props = { Prop(TEXT("Crate"), 1200.f, 215.f, TEXT("Doener")), Prop(TEXT("TrashCan"), 2500.f, 220.f, TEXT("Money")),
				Prop(TEXT("Crate"), 3700.f, 200.f, TEXT("Currywurst")), Prop(TEXT("Crate"), 4700.f, 215.f, TEXT("Money")),
				Prop(TEXT("TrashCan"), 5600.f, 225.f, TEXT("Doener")), Prop(TEXT("Crate"), 6900.f, 100.f, TEXT("Doener")) };
			S.Weapons = { Weapon(TEXT("Pipe"), 900.f, 160.f), Weapon(TEXT("Bat"), 3100.f, 60.f), Weapon(TEXT("Knife"), 5100.f, 140.f), Weapon(TEXT("Pipe"), 6600.f, 200.f) };
			Stages.Add(S);
		}
		return Stages;
	}

	TMap<FName, FWeaponDef> BuildWeapons()
	{
		TMap<FName, FWeaponDef> Out;
		auto Add = [&Out](const TCHAR* Type, const TCHAR* Name, float Dmg, float Reach, int32 Dur, EHitType Hit, float ThrowDmg, float Hold, float FPS)
		{
			FWeaponDef W;
			W.Type = FName(Type);
			W.DisplayName = Name;
			W.Damage = Dmg;
			W.Reach = Reach;
			W.Durability = Dur;
			W.HitType = Hit;
			W.ThrowDamage = ThrowDmg;
			W.HoldAngle = Hold;
			W.FPS = FPS;
			Out.Add(W.Type, W);
		};
		Add(TEXT("Pipe"), TEXT("ROHR"), 12.f, 140.f, 8, EHitType::Heavy, 14.f, 80.f, 13.f);
		Add(TEXT("Bat"), TEXT("SCHLÄGER"), 14.f, 150.f, 6, EHitType::Knockdown, 14.f, 80.f, 12.f);
		Add(TEXT("Knife"), TEXT("MESSER"), 9.f, 112.f, 12, EHitType::Light, 18.f, 70.f, 17.f);
		Add(TEXT("Bottle"), TEXT("FLASCHE"), 16.f, 110.f, 1, EHitType::Knockdown, 12.f, 80.f, 13.f);
		Add(TEXT("Golf"), TEXT("GOLFSCHLÄGER"), 13.f, 160.f, 10, EHitType::Knockdown, 14.f, 80.f, 12.f);
		return Out;
	}
}

namespace BrawlerData
{
	const TArray<FStageDef>& GetStages()
	{
		static const TArray<FStageDef> Stages = BuildStages();
		return Stages;
	}

	const FWeaponDef* GetWeapon(FName Type)
	{
		static const TMap<FName, FWeaponDef> Weapons = BuildWeapons();
		return Weapons.Find(Type);
	}

	bool IsWeapon(FName Type)
	{
		return GetWeapon(Type) != nullptr;
	}

	FBrawlerAttack MakeWeaponAttack(FName Type)
	{
		FBrawlerAttack A;
		A.Anim = TEXT("weapon_swing");
		A.ActiveStart = 2;
		A.ActiveEnd = 2;
		A.CancelFrame = 99;
		A.Hitstop = 0.11f;
		A.Weapon = Type;
		if (const FWeaponDef* W = GetWeapon(Type))
		{
			A.Damage = W->Damage;
			A.ReachMax = W->Reach;
			A.HitType = W->HitType;
			A.Knockback = W->HitType == EHitType::Knockdown ? 340.f : 90.f;
			A.Launch = W->HitType == EHitType::Knockdown ? 500.f : 0.f;
			A.FPS = W->FPS;
		}
		return A;
	}
}
