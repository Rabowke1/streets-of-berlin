#include "BrawlerEnemy.h"

#include "BrawlerGameMode.h"
#include "BrawlerPlayer.h"
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

	if (Type == TEXT("Kalle"))
	{
		P.DisplayName = TEXT("KALLE");
		P.Style = EEnemyStyle::Punk;
		P.MaxHealth = 55.f;
		P.WalkSpeed = 170.f;
		P.Score = 100;
	}
	else if (Type == TEXT("Ronny"))
	{
		P.DisplayName = TEXT("RONNY");
		P.Style = EEnemyStyle::Punk;
		P.MaxHealth = 70.f;
		P.WalkSpeed = 185.f;
		P.Score = 150;
		P.AttackCooldown = 1.1f;
	}
	else if (Type == TEXT("Jojo"))
	{
		P.DisplayName = TEXT("JOJO");
		P.Style = EEnemyStyle::Skater;
		P.MaxHealth = 50.f;
		P.WalkSpeed = 230.f;
		P.Score = 150;
	}
	else if (Type == TEXT("Deniz"))
	{
		P.DisplayName = TEXT("DENIZ");
		P.Style = EEnemyStyle::Skater;
		P.MaxHealth = 60.f;
		P.WalkSpeed = 250.f;
		P.Score = 200;
		P.AttackCooldown = 1.1f;
	}
	else if (Type == TEXT("Brecher"))
	{
		P.DisplayName = TEXT("BRECHER");
		P.Style = EEnemyStyle::Heavy;
		P.MaxHealth = 150.f;
		P.WalkSpeed = 120.f;
		P.Score = 500;
		P.bGrabbable = false;
		P.Armor = 2;
		P.AttackCooldown = 1.8f;
	}
	else if (Type == TEXT("Rolf"))
	{
		P.DisplayName = TEXT("TUERSTEHER ROLF");
		P.Style = EEnemyStyle::Boss;
		P.MaxHealth = 420.f;
		P.WalkSpeed = 140.f;
		P.Score = 5000;
		P.bGrabbable = false;
		P.Armor = 3;
		P.AttackCooldown = 1.3f;
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
	ShadowScale = (Profile.Style == EEnemyStyle::Heavy || Profile.Style == EEnemyStyle::Boss) ? 1.35f : 1.f;
	WaitDistance = FMath::FRandRange(200.f, 300.f);
	Cooldown = FMath::FRandRange(0.4f, 1.4f);
}

void ABrawlerEnemy::BeginPlay()
{
	Super::BeginPlay();
	Health = MaxHealth;
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

	switch (Profile.Style)
	{
	case EEnemyStyle::Heavy:
	case EEnemyStyle::Boss:
		A.Anim = TEXT("attack1");
		A.ActiveStart = 2;
		A.ActiveEnd = 2;
		A.Damage = (Profile.Style == EEnemyStyle::Boss ? 16.f : 13.f) * DamageScale;
		A.ReachMax = 118.f;
		A.HitType = EHitType::Knockdown;
		A.Knockback = 330.f;
		A.Launch = 500.f;
		A.Hitstop = 0.12f;
		A.FPS = Profile.Style == EEnemyStyle::Boss ? (bEnraged ? 11.f : 9.f) : 7.5f;
		A.DepthRange = 30.f;
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
	if (Profile.Style == EEnemyStyle::Skater)
	{
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
	}
	else
	{
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
	}
	return A;
}

void ABrawlerEnemy::BeginEnemyAttack(const FBrawlerAttack& Attack)
{
	StartAttack(Attack);
}

// ---------------------------------------------------------------------------
// KI
// ---------------------------------------------------------------------------
void ABrawlerEnemy::TickEntity(float DeltaSeconds)
{
	Cooldown -= DeltaSeconds;
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
		if (Profile.Style == EEnemyStyle::Skater && AbsDx > 170.f && AbsDx < 360.f && FMath::FRand() < 2.5f * DeltaSeconds)
		{
			BeginEnemyAttack(MakeRush());
			return;
		}
		if ((Profile.Style == EEnemyStyle::Heavy || IsBoss()) && AbsDx > 220.f && AbsDx < 560.f && FMath::FRand() < (IsBoss() ? 2.5f : 1.2f) * DeltaSeconds)
		{
			BeginEnemyAttack(MakeRush());
			return;
		}
	}

	// Nahkampf
	const float MeleeRange = (Profile.Style == EEnemyStyle::Heavy || IsBoss()) ? 105.f : 82.f;
	if (bReady && AbsDx < MeleeRange && AbsDx > 24.f && AbsDd < 12.f)
	{
		const bool bStrong = Profile.Style == EEnemyStyle::Punk && FMath::FRand() < 0.35f;
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
