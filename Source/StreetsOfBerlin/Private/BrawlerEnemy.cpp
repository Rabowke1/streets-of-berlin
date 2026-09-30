#include "BrawlerEnemy.h"

#include "BrawlerGameMode.h"
#include "BrawlerPlayer.h"
#include "BrawlerStageData.h"
#include "EngineUtils.h"

ABrawlerEnemy::ABrawlerEnemy()
{
	Team = EBrawlerTeam::Enemy;
	GetUpInvulnerability = 0.4f;
}

FEnemyProfile ABrawlerEnemy::GetProfile(FName Type)
{
	FEnemyProfile P;
	P.Type = Type;
	P.SpriteSet = Type.ToString();

	auto Set = [&P](const TCHAR* Name, EEnemyStyle Style, float Health, float Speed, int32 Score, float Cooldown)
	{
		P.DisplayName = Name;
		P.Style = Style;
		P.MaxHealth = Health;
		P.WalkSpeed = Speed;
		P.Score = Score;
		P.AttackCooldown = Cooldown;
	};

	if (Type == TEXT("Kalle"))        { Set(TEXT("KALLE"), EEnemyStyle::Punk, 55.f, 170.f, 100, 1.4f); }
	else if (Type == TEXT("Ronny"))   { Set(TEXT("RONNY"), EEnemyStyle::Punk, 70.f, 185.f, 150, 1.1f); }
	else if (Type == TEXT("Micha"))   { Set(TEXT("MESSER-MICHA"), EEnemyStyle::Punk, 70.f, 180.f, 250, 1.2f); P.Weapon = TEXT("Knife"); }
	else if (Type == TEXT("Jojo"))    { Set(TEXT("JOJO"), EEnemyStyle::Skater, 50.f, 230.f, 150, 1.4f); }
	else if (Type == TEXT("Deniz"))   { Set(TEXT("DENIZ"), EEnemyStyle::Skater, 60.f, 250.f, 200, 1.1f); }
	else if (Type == TEXT("Zoe"))     { Set(TEXT("ZOE"), EEnemyStyle::Kicker, 65.f, 240.f, 250, 1.0f); }
	else if (Type == TEXT("Nina"))    { Set(TEXT("NINA"), EEnemyStyle::Kicker, 75.f, 250.f, 300, 0.9f); }
	else if (Type == TEXT("Brecher")) { Set(TEXT("BRECHER"), EEnemyStyle::Heavy, 150.f, 120.f, 500, 1.8f); P.bGrabbable = false; P.Armor = 2; P.ShadowScale = 1.35f; }
	else if (Type == TEXT("Rolf"))
	{
		Set(TEXT("TUERSTEHER ROLF"), EEnemyStyle::Heavy, 420.f, 140.f, 5000, 1.3f);
		P.bGrabbable = false; P.Armor = 3; P.bBoss = true; P.ShadowScale = 1.4f;
	}
	else if (Type == TEXT("RolfII"))
	{
		Set(TEXT("ROLF (REVANCHE)"), EEnemyStyle::Heavy, 260.f, 150.f, 2000, 1.4f);
		P.SpriteSet = TEXT("Rolf"); P.bGrabbable = false; P.Armor = 3; P.ShadowScale = 1.4f;
	}
	else if (Type == TEXT("Sven"))
	{
		Set(TEXT("HOOL-SVEN"), EEnemyStyle::Heavy, 480.f, 150.f, 6000, 1.2f);
		P.bGrabbable = false; P.Armor = 3; P.bBoss = true; P.Weapon = TEXT("Bat"); P.ShadowScale = 1.4f;
	}
	else if (Type == TEXT("Harald"))
	{
		Set(TEXT("BAULOEWE HARALD"), EEnemyStyle::Suit, 560.f, 200.f, 10000, 1.0f);
		P.bGrabbable = false; P.Armor = 2; P.bBoss = true; P.Weapon = TEXT("Golf"); P.ShadowScale = 1.2f;
		P.Summons = { TEXT("Zoe"), TEXT("Brecher") };
	}
	else
	{
		P.DisplayName = Type.ToString().ToUpper();
	}
	return P;
}

void ABrawlerEnemy::InitFromProfile(FName Type)
{
	Profile = GetProfile(Type);
	SpriteSet = Profile.SpriteSet;
	DisplayName = Profile.DisplayName;
	MaxHealth = Profile.MaxHealth;
	Health = MaxHealth;
	WalkSpeed = Profile.WalkSpeed;
	DepthSpeed = Profile.WalkSpeed * 0.65f;
	bGrabbable = Profile.bGrabbable;
	Armor = Profile.Armor;
	SpriteScale = Profile.Scale;
	ShadowScale = Profile.ShadowScale;
	WaitDistance = FMath::FRandRange(200.f, 300.f);
	Cooldown = FMath::FRandRange(0.4f, 1.4f);
	ThrowCooldown = FMath::FRandRange(2.f, 4.f);
}

void ABrawlerEnemy::BeginPlay()
{
	Super::BeginPlay();
	Health = MaxHealth;
	if (!Profile.Weapon.IsNone())
	{
		// Gegner-Waffen halten, solange der Gegner steht
		TakeWeapon(Profile.Weapon, 999);
	}
}

void ABrawlerEnemy::SetEntering(bool bInEntering)
{
	bEntering = bInEntering;
	bClampToView = !bInEntering;
}

// ---------------------------------------------------------------------------
// Angriffe
// ---------------------------------------------------------------------------
FBrawlerAttack ABrawlerEnemy::MakeMelee(bool bStrong) const
{
	FBrawlerAttack A;
	const float DamageScale = bEnraged ? 1.3f : 1.f;

	if (HasWeapon())
	{
		A = BrawlerData::MakeWeaponAttack(GetWeapon());
		A.Damage = FMath::RoundToFloat(A.Damage * (IsBoss() ? 1.2f : 0.8f) * DamageScale);
		A.FPS = FMath::Max(8.f, A.FPS - 3.f);
		A.Weapon = NAME_None; // Gegner-Waffen nutzen sich nicht ab
		return A;
	}

	switch (Profile.Style)
	{
	case EEnemyStyle::Heavy:
		A.Anim = TEXT("attack1");
		A.ActiveStart = 2;
		A.ActiveEnd = 2;
		A.Damage = (IsBoss() ? 16.f : 13.f) * DamageScale;
		A.ReachMax = 118.f;
		A.HitType = EHitType::Knockdown;
		A.Knockback = 330.f;
		A.Launch = 500.f;
		A.Hitstop = 0.12f;
		A.FPS = IsBoss() ? (bEnraged ? 11.f : 9.f) : 7.5f;
		A.DepthRange = 30.f;
		break;

	case EEnemyStyle::Kicker:
		if (bStrong)
		{
			A.Anim = TEXT("attack2");
			A.ActiveStart = 1;
			A.ActiveEnd = 2;
			A.Damage = 10.f;
			A.ReachMax = 130.f;
			A.HitType = EHitType::Knockdown;
			A.Knockback = 300.f;
			A.Launch = 460.f;
			A.Lunge = 260.f;
			A.FPS = 11.f;
			A.Hitstop = 0.1f;
		}
		else
		{
			A.Anim = TEXT("attack1");
			A.Damage = 6.f;
			A.ReachMax = 118.f;
			A.Knockback = 60.f;
			A.FPS = 11.f;
			A.HeightMin = 20.f;
		}
		break;

	case EEnemyStyle::Suit:
		if (bStrong)
		{
			A.Anim = TEXT("attack4");
			A.ActiveStart = 1;
			A.ActiveEnd = 2;
			A.Damage = 14.f * DamageScale;
			A.ReachMax = 138.f;
			A.HitType = EHitType::Knockdown;
			A.Knockback = 380.f;
			A.Launch = 540.f;
			A.Lunge = 60.f;
			A.FPS = 12.f;
			A.Hitstop = 0.12f;
		}
		else
		{
			A.Anim = TEXT("attack3");
			A.ActiveStart = 1;
			A.ActiveEnd = 2;
			A.Damage = 9.f * DamageScale;
			A.ReachMax = 95.f;
			A.HitType = EHitType::Heavy;
			A.Knockback = 70.f;
			A.FPS = 13.f;
		}
		break;

	case EEnemyStyle::Punk:
		if (bStrong)
		{
			A.Anim = TEXT("attack2");
			A.ActiveStart = 2;
			A.ActiveEnd = 2;
			A.Damage = 9.f;
			A.ReachMax = 104.f;
			A.HitType = EHitType::Knockdown;
			A.Knockback = 260.f;
			A.Launch = 420.f;
			A.Hitstop = 0.1f;
			A.FPS = 9.f;
			A.Lunge = 80.f;
			break;
		}
		[[fallthrough]]; // sonst: Jab
	default:
		A.Anim = TEXT("attack1");
		A.ActiveStart = 1;
		A.ActiveEnd = 1;
		A.Damage = 5.f;
		A.ReachMax = 92.f;
		A.HitType = EHitType::Light;
		A.Knockback = 40.f;
		A.FPS = 9.f; // etwas langsamer als der Spieler -> lesbar
		break;
	}
	return A;
}

FBrawlerAttack ABrawlerEnemy::MakeRush() const
{
	FBrawlerAttack A;
	A.Anim = TEXT("attack2");
	switch (Profile.Style)
	{
	case EEnemyStyle::Skater:
		// Rutschkick ueber den Boden
		A.ActiveStart = 1;
		A.ActiveEnd = 2;
		A.Damage = 9.f;
		A.ReachMax = 110.f;
		A.HeightMin = 0.f;
		A.HeightMax = 90.f;
		A.HitType = EHitType::Knockdown;
		A.Knockback = 280.f;
		A.Launch = 380.f;
		A.Lunge = 640.f;
		A.FPS = 7.f;
		break;

	case EEnemyStyle::Kicker:
		// Fliegender Roundhouse-Kick
		A.ActiveStart = 1;
		A.ActiveEnd = 2;
		A.Damage = 11.f;
		A.ReachMax = 130.f;
		A.HitType = EHitType::Knockdown;
		A.Knockback = 320.f;
		A.Launch = 480.f;
		A.Lunge = 520.f;
		A.FPS = 9.f;
		break;

	case EEnemyStyle::Suit:
		// Sprungkick
		A.Anim = TEXT("jump_kick");
		A.ActiveStart = 1;
		A.ActiveEnd = 1;
		A.Damage = 14.f;
		A.ReachMax = 120.f;
		A.HeightMin = -40.f;
		A.HeightMax = 150.f;
		A.HitType = EHitType::Knockdown;
		A.Knockback = 340.f;
		A.Launch = 480.f;
		A.Hitstop = 0.1f;
		A.bJump = true;
		break;

	default:
		// Sturmangriff (Schulter voraus)
		A.ActiveStart = 0;
		A.ActiveEnd = 3;
		A.bLoopAnim = true;
		A.Duration = IsBoss() ? 1.3f : 1.0f;
		A.Damage = IsBoss() ? 18.f : 14.f;
		A.ReachMax = 80.f;
		A.HitType = EHitType::Knockdown;
		A.Knockback = 420.f;
		A.Launch = 540.f;
		A.Lunge = IsBoss() ? (bEnraged ? 700.f : 600.f) : 520.f;
		A.FPS = 12.f;
		A.DepthRange = 32.f;
		A.Hitstop = 0.12f;
		break;
	}
	return A;
}

void ABrawlerEnemy::BeginEnemyAttack(const FBrawlerAttack& Attack)
{
	StartAttack(Attack);
	if (Attack.bJump)
	{
		VelZ = 780.f;
		Height = 0.1f;
		VelX = Facing * 520.f;
	}
}

// ---------------------------------------------------------------------------
// KI
// ---------------------------------------------------------------------------
void ABrawlerEnemy::TickEntity(float DeltaSeconds)
{
	Cooldown -= DeltaSeconds;
	ThrowCooldown -= DeltaSeconds;
	Super::TickEntity(DeltaSeconds);

	if (State == EFighterState::Dead && StateTime > 1.2f)
	{
		Destroy();
	}
}

void ABrawlerEnemy::TickControl(float DeltaSeconds)
{
	ABrawlerGameMode* GM = GetBrawlerGameMode();
	ABrawlerPlayer* Player = GM ? GM->GetPlayer() : nullptr;

	auto SetWalking = [this](float VX, float VD)
	{
		VelX = VX;
		VelDepth = VD;
		const bool bMoving = FMath::Abs(VX) > 5.f || FMath::Abs(VD) > 5.f;
		if (bMoving && State != EFighterState::Walk)
		{
			EnterState(EFighterState::Walk);
			VelX = VX;
			VelDepth = VD;
		}
		else if (!bMoving && State != EFighterState::Idle)
		{
			EnterState(EFighterState::Idle);
		}
	};

	if (!GM)
	{
		return;
	}

	// Ins Bild laufen
	if (bEntering)
	{
		const float Center = GM->GetCameraX();
		const bool bInside = PosX > GM->GetViewMinX() + 60.f && PosX < GM->GetViewMaxX() - 60.f;
		if (bInside)
		{
			SetEntering(false);
		}
		else
		{
			Facing = FMath::Sign(Center - PosX);
			SetWalking(Facing * WalkSpeed, 0.f);
			return;
		}
	}

	if (!Player || !Player->IsAlive() || Player->GetState() == EFighterState::Victory)
	{
		if (bHasToken)
		{
			GM->ReleaseAttackToken(this);
			bHasToken = false;
		}
		SetWalking(0.f, 0.f);
		return;
	}

	const float Dx = Player->PosX - PosX;
	const float Dd = Player->Depth - Depth;
	if (FMath::Abs(Dx) > 8.f)
	{
		Facing = FMath::Sign(Dx);
	}

	if (!bEnraged && IsBoss() && Health < MaxHealth * 0.5f)
	{
		bEnraged = true;
		WalkSpeed *= 1.3f;
		DepthSpeed *= 1.3f;
		Profile.AttackCooldown *= 0.7f;
	}

	// Boss ruft Verstaerkung (bei 66 % und 33 % Energie)
	if (Profile.Summons.Num() > 0 && SummonCount < 2 && Health < MaxHealth * (SummonCount == 0 ? 0.66f : 0.33f))
	{
		++SummonCount;
		GM->PlaySfx(TEXT("SFX_Go"), 0.6f, 0.f);
		for (const FName& Type : Profile.Summons)
		{
			const float X = (SummonCount % 2) ? GM->GetViewMinX() - 80.f : GM->GetViewMaxX() + 80.f;
			if (ABrawlerEnemy* Minion = GM->SpawnEnemy(Type, X, FMath::FRandRange(30.f, 210.f)))
			{
				Minion->SetEntering(true);
			}
		}
	}

	ThinkTimer -= DeltaSeconds;
	if (ThinkTimer <= 0.f)
	{
		ThinkTimer = FMath::FRandRange(0.35f, 0.9f);
		Side = PosX < Player->PosX ? -1.f : 1.f;
		// Ab und zu die Seite wechseln, um den Spieler einzukreisen
		if (FMath::FRand() < 0.12f)
		{
			Side = -Side;
		}
		DepthOffset = FMath::FRandRange(-1.f, 1.f);
	}

	// Token jedes Mal neu anfragen: der GameMode raeumt Tokens umgefallener Gegner selbst ab
	if (Cooldown <= 0.f)
	{
		bHasToken = GM->RequestAttackToken(this);
	}

	const bool bPlayerAttackable = !Player->IsDowned() && Player->GetState() != EFighterState::Grabbed;
	const bool bReady = bHasToken && Cooldown <= 0.f && bPlayerAttackable;
	const float AbsDx = FMath::Abs(Dx);
	const float AbsDd = FMath::Abs(Dd);

	// Distanz-Angriffe
	if (bReady && AbsDd < 12.f)
	{
		// Messer werfen
		if (GetWeapon() == FName(TEXT("Knife")) && !IsBoss() && AbsDx > 250.f && AbsDx < 520.f && ThrowCooldown <= 0.f && FMath::FRand() < 1.5f * DeltaSeconds)
		{
			ThrowCooldown = 6.f;
			FBrawlerAttack Throw;
			Throw.Anim = TEXT("weapon_throw");
			Throw.ActiveStart = 99;
			Throw.ActiveEnd = 99;
			Throw.Damage = 0.f;
			Throw.FPS = 9.f;
			Throw.bWhoosh = false;
			BeginEnemyAttack(Throw);
			return;
		}

		float RushChance = 0.f, RushMin = 0.f, RushMax = 0.f;
		switch (Profile.Style)
		{
		case EEnemyStyle::Skater: RushChance = 2.5f; RushMin = 170.f; RushMax = 360.f; break;
		case EEnemyStyle::Kicker: RushChance = 1.4f; RushMin = 180.f; RushMax = 320.f; break;
		case EEnemyStyle::Heavy:  RushChance = IsBoss() ? 2.5f : 1.2f; RushMin = 220.f; RushMax = 560.f; break;
		case EEnemyStyle::Suit:   RushChance = 1.6f; RushMin = 200.f; RushMax = 380.f; break;
		default: break;
		}
		if (RushChance > 0.f && AbsDx > RushMin && AbsDx < RushMax && FMath::FRand() < RushChance * DeltaSeconds)
		{
			BeginEnemyAttack(MakeRush());
			return;
		}
	}

	// Nahkampf
	float MeleeRange = 82.f;
	if (const FWeaponDef* W = BrawlerData::GetWeapon(GetWeapon()))
	{
		MeleeRange = W->Reach * 0.8f;
	}
	else if (Profile.Style == EEnemyStyle::Heavy || Profile.Style == EEnemyStyle::Kicker)
	{
		MeleeRange = 105.f;
	}
	else if (Profile.Style == EEnemyStyle::Suit)
	{
		MeleeRange = 100.f;
	}

	if (bReady && AbsDx < MeleeRange && AbsDx > 24.f && AbsDd < 12.f)
	{
		const bool bStrong = (Profile.Style == EEnemyStyle::Punk && FMath::FRand() < 0.35f)
			|| (Profile.Style == EEnemyStyle::Kicker && FMath::FRand() < 0.3f)
			|| (Profile.Style == EEnemyStyle::Suit && FMath::FRand() < 0.35f);
		BeginEnemyAttack(MakeMelee(bStrong));
		return;
	}

	// Zielposition bestimmen
	float TargetX;
	float TargetD;
	if (bReady)
	{
		TargetX = Player->PosX + Side * (MeleeRange * 0.75f);
		TargetD = Player->Depth;
	}
	else
	{
		TargetX = Player->PosX + Side * WaitDistance;
		TargetD = Player->Depth + DepthOffset * 60.f;
	}
	TargetD = FMath::Clamp(TargetD, Brawler::DepthMin, Brawler::DepthMax);

	float MoveX = TargetX - PosX;
	float MoveD = TargetD - Depth;

	// Abstand zu anderen Gegnern halten
	for (TActorIterator<ABrawlerEnemy> It(GetWorld()); It; ++It)
	{
		ABrawlerEnemy* Other = *It;
		if (Other == this || !Other->IsAlive())
		{
			continue;
		}
		const float Ox = PosX - Other->PosX;
		const float Od = Depth - Other->Depth;
		if (FMath::Abs(Ox) < 60.f && FMath::Abs(Od) < 24.f)
		{
			MoveD += (Od >= 0.f ? 1.f : -1.f) * 40.f;
			MoveX += (Ox >= 0.f ? 1.f : -1.f) * 30.f;
		}
	}

	const float VX = FMath::Abs(MoveX) > 12.f ? FMath::Clamp(MoveX * 4.f, -WalkSpeed, WalkSpeed) : 0.f;
	const float VD = FMath::Abs(MoveD) > 6.f ? FMath::Clamp(MoveD * 4.f, -DepthSpeed, DepthSpeed) : 0.f;
	SetWalking(VX, VD);

	// Beim Rueckwaertsgehen weiter zum Spieler schauen
	if (FMath::Abs(Dx) > 8.f)
	{
		Facing = FMath::Sign(Dx);
	}
}

void ABrawlerEnemy::OnLanded()
{
	// Gegner-Waffen haben begrenzte Haltbarkeit, sobald sie fallen gelassen werden
	Super::OnLanded();
}

void ABrawlerEnemy::OnAttackFinished()
{
	Cooldown = Profile.AttackCooldown * FMath::FRandRange(0.8f, 1.35f);
	if (bHasToken)
	{
		if (ABrawlerGameMode* GM = GetBrawlerGameMode())
		{
			GM->ReleaseAttackToken(this);
		}
		bHasToken = false;
	}
}

void ABrawlerEnemy::OnHurt(ABrawlerFighter* Attacker, float Damage)
{
	Cooldown = FMath::Max(Cooldown, 0.5f);
	bEntering = false;
	bClampToView = true;
	if (HasWeapon() && WeaponDurability > 50)
	{
		// Faellt der Gegner gleich um, hat die fallengelassene Waffe normale Haltbarkeit
		if (const FWeaponDef* W = BrawlerData::GetWeapon(GetWeapon()))
		{
			WeaponDurability = W->Durability;
		}
	}
	if (bHasToken)
	{
		if (ABrawlerGameMode* GM = GetBrawlerGameMode())
		{
			GM->ReleaseAttackToken(this);
		}
		bHasToken = false;
	}
}

void ABrawlerEnemy::OnDied()
{
	if (ABrawlerGameMode* GM = GetBrawlerGameMode())
	{
		if (bHasToken)
		{
			GM->ReleaseAttackToken(this);
			bHasToken = false;
		}
		GM->OnEnemyKilled(this);
	}
}
