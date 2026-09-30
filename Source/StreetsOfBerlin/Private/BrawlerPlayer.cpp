#include "BrawlerPlayer.h"

#include "BrawlerEnemy.h"
#include "BrawlerGameMode.h"
#include "BrawlerPickup.h"
#include "BrawlerStageData.h"
#include "BrawlerWeaponItem.h"
#include "EngineUtils.h"

namespace
{
	FBrawlerAttack MakeAttack(const TCHAR* Anim, int32 Start, int32 End, float Damage, float ReachMax, EHitType Type)
	{
		FBrawlerAttack A;
		A.Anim = FName(Anim);
		A.ActiveStart = Start;
		A.ActiveEnd = End;
		A.Damage = Damage;
		A.ReachMin = 0.f;
		A.ReachMax = ReachMax;
		A.HitType = Type;
		return A;
	}
}

ABrawlerPlayer::ABrawlerPlayer()
{
	Team = EBrawlerTeam::Player;
	SpriteSet = TEXT("Kai");
	DisplayName = TEXT("KAI");
	MaxHealth = 120.f;
	WalkSpeed = 280.f;
	DepthSpeed = 180.f;
	GetUpInvulnerability = 1.2f;
}

void ABrawlerPlayer::BeginPlay()
{
	Super::BeginPlay();
	Facing = 1.f;
}

// ---------------------------------------------------------------------------
// Angriffsdaten
// ---------------------------------------------------------------------------
const FBrawlerAttack& ABrawlerPlayer::ComboAttack(int32 Step)
{
	static TArray<FBrawlerAttack> Combo = []()
	{
		TArray<FBrawlerAttack> Out;

		FBrawlerAttack Jab = MakeAttack(TEXT("attack1"), 1, 1, 4.f, 98.f, EHitType::Light);
		Jab.Knockback = 30.f;
		Jab.CancelFrame = 1;
		Jab.Hitstop = 0.06f;
		Out.Add(Jab);

		FBrawlerAttack Cross = MakeAttack(TEXT("attack2"), 1, 1, 5.f, 104.f, EHitType::Light);
		Cross.Knockback = 40.f;
		Cross.Lunge = 90.f;
		Cross.CancelFrame = 1;
		Cross.Hitstop = 0.07f;
		Out.Add(Cross);

		FBrawlerAttack Upper = MakeAttack(TEXT("attack3"), 1, 2, 7.f, 92.f, EHitType::Heavy);
		Upper.Knockback = 60.f;
		Upper.CancelFrame = 2;
		Upper.Hitstop = 0.09f;
		Out.Add(Upper);

		FBrawlerAttack Kick = MakeAttack(TEXT("attack4"), 1, 2, 11.f, 138.f, EHitType::Knockdown);
		Kick.Knockback = 360.f;
		Kick.Launch = 540.f;
		Kick.Lunge = 60.f;
		Kick.Hitstop = 0.12f;
		Kick.CancelFrame = 99;
		Out.Add(Kick);
		return Out;
	}();
	return Combo[FMath::Clamp(Step, 0, Combo.Num() - 1)];
}

const FBrawlerAttack& ABrawlerPlayer::JumpKickAttack()
{
	static FBrawlerAttack A = []()
	{
		FBrawlerAttack K = MakeAttack(TEXT("jump_kick"), 1, 1, 10.f, 120.f, EHitType::Knockdown);
		K.HeightMin = -40.f;
		K.HeightMax = 140.f;
		K.Knockback = 300.f;
		K.Launch = 420.f;
		K.Hitstop = 0.09f;
		return K;
	}();
	return A;
}

const FBrawlerAttack& ABrawlerPlayer::SpecialAttack()
{
	static FBrawlerAttack A = []()
	{
		FBrawlerAttack S = MakeAttack(TEXT("special"), 1, 4, 14.f, 130.f, EHitType::Knockdown);
		S.bHitsBothSides = true;
		S.DepthRange = 42.f;
		S.Knockback = 400.f;
		S.Launch = 560.f;
		S.Hitstop = 0.1f;
		S.bInvulnerable = true;
		S.HealthCost = 10.f;
		S.CancelFrame = 99;
		return S;
	}();
	return A;
}

const FBrawlerAttack& ABrawlerPlayer::BackAttack()
{
	static FBrawlerAttack A = []()
	{
		FBrawlerAttack B = MakeAttack(TEXT("back_attack"), 1, 1, 9.f, 105.f, EHitType::Knockdown);
		B.bHitsBehind = true;
		B.Knockback = 300.f;
		B.Launch = 420.f;
		B.Hitstop = 0.1f;
		B.CancelFrame = 99;
		return B;
	}();
	return A;
}

const FBrawlerAttack& ABrawlerPlayer::KneeAttack(bool bFinisher)
{
	static FBrawlerAttack Knee = []()
	{
		FBrawlerAttack K = MakeAttack(TEXT("grab_knee"), 1, 1, 6.f, 90.f, EHitType::Light);
		K.HeightMin = 20.f;
		K.Hitstop = 0.08f;
		K.bWhoosh = false;
		return K;
	}();
	static FBrawlerAttack Final = []()
	{
		FBrawlerAttack K = MakeAttack(TEXT("grab_knee"), 1, 1, 10.f, 90.f, EHitType::Knockdown);
		K.HeightMin = 20.f;
		K.Knockback = 320.f;
		K.Launch = 520.f;
		K.Hitstop = 0.12f;
		K.bWhoosh = false;
		return K;
	}();
	return bFinisher ? Final : Knee;
}

const FBrawlerAttack& ABrawlerPlayer::ThrowAttack()
{
	static FBrawlerAttack A = []()
	{
		FBrawlerAttack T;
		T.Anim = TEXT("throw");
		T.ActiveStart = 99; // kein Hitbox – der Wurf selbst passiert per Frame-Event
		T.ActiveEnd = 99;
		T.Damage = 0.f;
		T.bInvulnerable = true;
		return T;
	}();
	return A;
}

// ---------------------------------------------------------------------------
// Tick
// ---------------------------------------------------------------------------
void ABrawlerPlayer::TickEntity(float DeltaSeconds)
{
	AttackBuffer = FMath::Max(0.f, AttackBuffer - DeltaSeconds);
	JumpBuffer = FMath::Max(0.f, JumpBuffer - DeltaSeconds);
	SpecialBuffer = FMath::Max(0.f, SpecialBuffer - DeltaSeconds);
	BackBuffer = FMath::Max(0.f, BackBuffer - DeltaSeconds);
	GrabCooldown = FMath::Max(0.f, GrabCooldown - DeltaSeconds);

	// Combo-Ketten waehrend eines Angriffs
	if (State == EFighterState::Attack && Height <= 0.f)
	{
		if (SpecialBuffer > 0.f && bAttackConnected && CurrentAttack.Anim != SpecialAttack().Anim && Health > SpecialAttack().HealthCost + 1.f)
		{
			// Spezial-Cancel wie in SoR4
			SpecialBuffer = 0.f;
			StartSpecial();
		}
		else if (bInComboAttack && AttackBuffer > 0.f && bAttackConnected && ComboStep < 3 && AnimFrame >= CurrentAttack.CancelFrame && AnimFrame > CurrentAttack.ActiveEnd - 1 && StateTime > 0.08f)
		{
			AttackBuffer = 0.f;
			StartCombo(ComboStep + 1);
		}
	}

	// Wurf: Gegner wird bei Frame 2 losgelassen
	if (State == EFighterState::Attack && CurrentAttack.Anim == ThrowAttack().Anim && !bThrowReleased)
	{
		if (ABrawlerFighter* Partner = GrabPartner.Get())
		{
			Partner->PosX = PosX + Facing * (AnimFrame >= 1 ? 10.f : 40.f);
			Partner->Height = AnimFrame >= 1 ? 90.f : 20.f;
			if (AnimFrame >= 2)
			{
				bThrowReleased = true;
				GrabPartner.Reset();
				Partner->Height = 60.f;
				Partner->PosX = PosX + Facing * 30.f;
				Partner->GetThrown(this, Facing);
				if (ABrawlerGameMode* GM = GetBrawlerGameMode())
				{
					GM->PlaySfx(TEXT("SFX_Whoosh"), 0.8f, 0.1f);
				}
			}
		}
	}

	Super::TickEntity(DeltaSeconds);
}

void ABrawlerPlayer::TickControl(float DeltaSeconds)
{
	switch (State)
	{
	case EFighterState::Idle:
	case EFighterState::Walk:
		TickGroundControl(DeltaSeconds);
		break;

	case EFighterState::Jump:
		if (AttackBuffer > 0.f && !bJumpAttackUsed)
		{
			AttackBuffer = 0.f;
			bJumpAttackUsed = true;
			bInComboAttack = false;
			StartAttack(JumpKickAttack());
		}
		break;

	case EFighterState::Grabbing:
		TickGrabControl();
		break;

	default:
		break;
	}
}

void ABrawlerPlayer::TickGroundControl(float DeltaSeconds)
{
	if (JumpBuffer > 0.f)
	{
		JumpBuffer = 0.f;
		bJumpAttackUsed = false;
		VelZ = 860.f;
		VelX = MoveInput.X * WalkSpeed * 1.05f;
		VelDepth = MoveInput.Y * DepthSpeed * 0.6f;
		if (FMath::Abs(MoveInput.X) > 0.2f)
		{
			Facing = FMath::Sign(MoveInput.X);
		}
		Height = 0.1f;
		EnterState(EFighterState::Jump);
		return;
	}

	if (SpecialBuffer > 0.f)
	{
		SpecialBuffer = 0.f;
		if (Health > SpecialAttack().HealthCost + 1.f)
		{
			StartSpecial();
			return;
		}
	}

	if (BackBuffer > 0.f)
	{
		BackBuffer = 0.f;
		bInComboAttack = false;
		if (HasWeapon())
		{
			// Mit Waffe: Rueckschlag-Taste wirft die Waffe
			FBrawlerAttack Throw;
			Throw.Anim = TEXT("weapon_throw");
			Throw.ActiveStart = 99;
			Throw.ActiveEnd = 99;
			Throw.Damage = 0.f;
			Throw.FPS = 12.f;
			Throw.bWhoosh = false;
			StartAttack(Throw);
			return;
		}
		StartAttack(BackAttack());
		return;
	}

	if (AttackBuffer > 0.f)
	{
		AttackBuffer = 0.f;
		if (TryPickup())
		{
			return;
		}
		if (HasWeapon())
		{
			bInComboAttack = false;
			if (FMath::Abs(MoveInput.X) > 0.2f)
			{
				Facing = FMath::Sign(MoveInput.X);
			}
			StartAttack(BrawlerData::MakeWeaponAttack(GetWeapon()));
			return;
		}
		StartCombo(0);
		return;
	}

	// Bewegung
	VelX = MoveInput.X * WalkSpeed;
	VelDepth = MoveInput.Y * DepthSpeed;
	if (FMath::Abs(MoveInput.X) > 0.2f)
	{
		Facing = FMath::Sign(MoveInput.X);
	}

	const bool bMoving = MoveInput.SizeSquared() > 0.04f;
	if (bMoving && State != EFighterState::Walk)
	{
		EnterState(EFighterState::Walk);
		VelX = MoveInput.X * WalkSpeed;
		VelDepth = MoveInput.Y * DepthSpeed;
	}
	else if (!bMoving && State != EFighterState::Idle)
	{
		EnterState(EFighterState::Idle);
	}

	// In einen Gegner hineinlaufen -> Griff (nicht mit Waffe in der Hand)
	if (bMoving && FMath::Abs(MoveInput.X) > 0.5f && !HasWeapon())
	{
		WalkIntoTimer += DeltaSeconds;
		if (WalkIntoTimer > 0.12f && TryGrab())
		{
			WalkIntoTimer = 0.f;
		}
	}
	else
	{
		WalkIntoTimer = 0.f;
	}
}

void ABrawlerPlayer::TickGrabControl()
{
	ABrawlerFighter* Partner = GrabPartner.Get();
	if (!Partner)
	{
		return;
	}

	if (JumpBuffer > 0.f)
	{
		JumpBuffer = 0.f;
		ReleaseGrab();
		GrabCooldown = 0.6f;
		EnterState(EFighterState::Idle);
		return;
	}

	if (AttackBuffer > 0.f)
	{
		AttackBuffer = 0.f;
		const bool bHoldingAway = FMath::Abs(MoveInput.X) > 0.5f && FMath::Sign(MoveInput.X) != Facing;
		bInComboAttack = false;
		bAttackFromGrab = true;
		if (bHoldingAway)
		{
			// Umdrehen und in Laufrichtung werfen
			Facing = -Facing;
			Partner->PosX = PosX + Facing * 40.f;
			Partner->Facing = -Facing;
			bThrowReleased = false;
			StartAttack(ThrowAttack());
		}
		else
		{
			++KneeCount;
			StartAttack(KneeAttack(KneeCount >= 3));
		}
	}
}

void ABrawlerPlayer::StartCombo(int32 Step)
{
	ComboStep = Step;
	bInComboAttack = true;
	bAttackFromGrab = false;
	if (FMath::Abs(MoveInput.X) > 0.2f)
	{
		Facing = FMath::Sign(MoveInput.X);
	}
	StartAttack(ComboAttack(Step));
}

void ABrawlerPlayer::StartSpecial()
{
	bInComboAttack = false;
	bAttackFromGrab = false;
	ReleaseGrab();
	RecoverableHealth = FMath::Min(RecoverableHealth + SpecialAttack().HealthCost, MaxHealth);
	StartAttack(SpecialAttack());
	if (ABrawlerGameMode* GM = GetBrawlerGameMode())
	{
		GM->PlaySfx(TEXT("SFX_Special"), 0.9f, 0.05f);
		GM->SpawnEffect(TEXT("FX_SpecialRing"), PosX, Depth, 20.f, Facing, 12.f);
	}
}

bool ABrawlerPlayer::TryPickup()
{
	// Naechsten Gegenstand (Essen, Geld oder Waffe) unter der Figur suchen
	ABrawlerEntity* Best = nullptr;
	float BestDist = 1e9f;
	for (TActorIterator<ABrawlerEntity> It(GetWorld()); It; ++It)
	{
		ABrawlerEntity* E = *It;
		const ABrawlerPickup* Pickup = Cast<ABrawlerPickup>(E);
		const ABrawlerWeaponItem* Item = Cast<ABrawlerWeaponItem>(E);
		if ((Pickup && !Pickup->CanCollect()) || (Item && !Item->CanCollect()) || (!Pickup && !Item))
		{
			continue;
		}
		const float Dist = FMath::Abs(E->PosX - PosX);
		if (Dist < 64.f && FMath::Abs(E->Depth - Depth) < 28.f && Dist < BestDist)
		{
			Best = E;
			BestDist = Dist;
		}
	}
	if (!Best)
	{
		return false;
	}
	if (ABrawlerWeaponItem* Item = Cast<ABrawlerWeaponItem>(Best))
	{
		if (HasWeapon())
		{
			DropWeapon(false);
		}
		Item->Collect(this);
	}
	else if (ABrawlerPickup* Pickup = Cast<ABrawlerPickup>(Best))
	{
		Pickup->Collect(this);
	}
	EnterState(EFighterState::Pickup);
	return true;
}

bool ABrawlerPlayer::TryGrab()
{
	if (GrabCooldown > 0.f)
	{
		return false;
	}
	for (TActorIterator<ABrawlerEnemy> It(GetWorld()); It; ++It)
	{
		ABrawlerEnemy* Enemy = *It;
		if (!Enemy->bGrabbable || !Enemy->IsAlive())
		{
			continue;
		}
		const EFighterState S = Enemy->GetState();
		if (S != EFighterState::Idle && S != EFighterState::Walk && S != EFighterState::Hurt)
		{
			continue;
		}
		const float Fwd = (Enemy->PosX - PosX) * Facing;
		if (Fwd > 15.f && Fwd < 66.f && FMath::Abs(Enemy->Depth - Depth) < 16.f && Enemy->Height <= 0.f)
		{
			KneeCount = 0;
			StartGrab(Enemy);
			return true;
		}
	}
	return false;
}

// ---------------------------------------------------------------------------
// Callbacks
// ---------------------------------------------------------------------------
void ABrawlerPlayer::OnAttackHit(ABrawlerEntity* Target, const FBrawlerAttack& Attack)
{
	// Rueckgewinnbare Energie (gruener Balken) durch Treffer zurueckholen
	if (RecoverableHealth > 0.f && Cast<ABrawlerFighter>(Target))
	{
		const float Regain = FMath::Min(RecoverableHealth, Attack.Damage * 0.6f);
		RecoverableHealth -= Regain;
		Heal(Regain);
	}
}

void ABrawlerPlayer::OnAttackFinished()
{
	if (bAttackFromGrab)
	{
		bAttackFromGrab = false;
		ABrawlerFighter* Partner = GrabPartner.Get();
		if (Partner && Partner->GetState() == EFighterState::Grabbed && CurrentAttack.Anim != ThrowAttack().Anim)
		{
			State = EFighterState::Grabbing;
			StateTime = 0.f;
			PlayCharAnim(TEXT("grab"), true);
			return;
		}
		GrabPartner.Reset();
		GrabCooldown = 0.5f;
	}
	if (CurrentAttack.Anim != FName(TEXT("attack1")) || !bAttackConnected)
	{
		ComboStep = 0;
	}
}

void ABrawlerPlayer::OnHurt(ABrawlerFighter* Attacker, float Damage)
{
	RecoverableHealth = 0.f;
	ComboStep = 0;
	bInComboAttack = false;
	bAttackFromGrab = false;
}

void ABrawlerPlayer::OnLanded()
{
	bJumpAttackUsed = false;
	Super::OnLanded();
}

void ABrawlerPlayer::OnDied()
{
	if (ABrawlerGameMode* GM = GetBrawlerGameMode())
	{
		GM->OnPlayerDied();
	}
}

void ABrawlerPlayer::Celebrate()
{
	ReleaseGrab();
	EnterState(EFighterState::Victory);
}

void ABrawlerPlayer::DropIn()
{
	Health = MaxHealth;
	RecoverableHealth = 0.f;
	Height = 600.f;
	VelZ = -200.f;
	VelX = 0.f;
	bJumpAttackUsed = true;
	MakeInvulnerable(2.5f);
	Weapon = NAME_None;
	EnterState(EFighterState::Jump);

	// Gegner in der Naehe werden umgeworfen (wie beim Wiedereinstieg in SoR)
	for (TActorIterator<ABrawlerEnemy> It(GetWorld()); It; ++It)
	{
		ABrawlerEnemy* Enemy = *It;
		if (Enemy->IsAlive() && !Enemy->IsDowned() && FMath::Abs(Enemy->PosX - PosX) < 350.f)
		{
			Enemy->Knockdown(FMath::Sign(Enemy->PosX - PosX + 0.01f), 300.f, 450.f);
		}
	}
}
