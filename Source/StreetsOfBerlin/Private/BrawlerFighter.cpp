#include "BrawlerFighter.h"

#include "BrawlerGameMode.h"
#include "BrawlerAssets.h"
#include "BrawlerStageData.h"
#include "BrawlerWeaponItem.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "PaperSprite.h"
#include "PaperSpriteComponent.h"

ABrawlerFighter::ABrawlerFighter()
{
	WeaponSprite = CreateDefaultSubobject<UPaperSpriteComponent>(TEXT("WeaponSprite"));
	WeaponSprite->SetupAttachment(Root);
	WeaponSprite->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	WeaponSprite->SetGenerateOverlapEvents(false);
	WeaponSprite->CastShadow = false;
	WeaponSprite->SetVisibility(false);
}

void ABrawlerFighter::BeginPlay()
{
	Super::BeginPlay();
	Health = MaxHealth;
	if (UBrawlerAssets* Assets = UBrawlerAssets::Get(this))
	{
		if (UMaterialInterface* Mat = Assets->GetSpriteMaterial())
		{
			WeaponSprite->SetMaterial(0, Mat);
		}
	}
	EnterState(EFighterState::Idle);
}

ABrawlerGameMode* ABrawlerFighter::GetBrawlerGameMode() const
{
	return GetWorld() ? Cast<ABrawlerGameMode>(GetWorld()->GetAuthGameMode()) : nullptr;
}

// ---------------------------------------------------------------------------
// Animationen
// ---------------------------------------------------------------------------
void ABrawlerFighter::GetAnimInfo(FName Anim, float& OutFPS, bool& bOutLoop)
{
	struct FInfo { const TCHAR* Name; float FPS; bool bLoop; };
	static const FInfo Table[] =
	{
		{ TEXT("idle"), 7.f, true },
		{ TEXT("walk"), 11.f, true },
		{ TEXT("hurt"), 10.f, false },
		{ TEXT("grabbed"), 5.f, true },
		{ TEXT("fall"), 8.f, false },
		{ TEXT("down"), 1.f, false },
		{ TEXT("getup"), 7.f, false },
		{ TEXT("attack1"), 15.f, false },
		{ TEXT("attack2"), 14.f, false },
		{ TEXT("attack3"), 14.f, false },
		{ TEXT("attack4"), 13.f, false },
		{ TEXT("jump"), 0.f, false },
		{ TEXT("jump_kick"), 14.f, false },
		{ TEXT("special"), 16.f, false },
		{ TEXT("back_attack"), 14.f, false },
		{ TEXT("grab"), 1.f, true },
		{ TEXT("grab_knee"), 14.f, false },
		{ TEXT("throw"), 11.f, false },
		{ TEXT("pickup"), 1.f, false },
		{ TEXT("victory"), 4.f, true },
	};

	for (const FInfo& Info : Table)
	{
		if (Anim == FName(Info.Name))
		{
			OutFPS = Info.FPS;
			bOutLoop = Info.bLoop;
			return;
		}
	}
	OutFPS = 10.f;
	bOutLoop = false;
}

void ABrawlerFighter::PlayCharAnim(FName Anim, bool bRestart, float FPSOverride)
{
	float FPS;
	bool bLoop;
	GetAnimInfo(Anim, FPS, bLoop);
	if (FPSOverride > 0.f)
	{
		FPS = FPSOverride;
	}
	PlayFrames(SpriteSet, SpriteSet + TEXT("_") + Anim.ToString(), FPS, bLoop, bRestart);
}

// ---------------------------------------------------------------------------
// Zustandsmaschine
// ---------------------------------------------------------------------------
void ABrawlerFighter::EnterState(EFighterState NewState)
{
	const EFighterState Old = State;
	State = NewState;
	StateTime = 0.f;

	switch (NewState)
	{
	case EFighterState::Idle:
		VelX = VelDepth = 0.f;
		PlayCharAnim(TEXT("idle"));
		break;
	case EFighterState::Walk:
		PlayCharAnim(TEXT("walk"));
		break;
	case EFighterState::Hurt:
		PlayCharAnim(TEXT("hurt"), true);
		break;
	case EFighterState::Grabbed:
		VelX = VelDepth = 0.f;
		PlayCharAnim(TEXT("grabbed"), true);
		break;
	case EFighterState::Grabbing:
		VelX = VelDepth = 0.f;
		GrabTimer = 0.f;
		PlayCharAnim(TEXT("grab"), Old != EFighterState::Attack);
		break;
	case EFighterState::Falling:
		PlayCharAnim(TEXT("fall"), true);
		break;
	case EFighterState::Down:
		VelX = VelDepth = VelZ = 0.f;
		Height = 0.f;
		PlayCharAnim(TEXT("down"), true);
		break;
	case EFighterState::GetUp:
		PlayCharAnim(TEXT("getup"), true);
		break;
	case EFighterState::Pickup:
		VelX = VelDepth = 0.f;
		PlayCharAnim(TEXT("pickup"), true);
		break;
	case EFighterState::Dead:
		VelX = VelDepth = VelZ = 0.f;
		PlayCharAnim(TEXT("down"));
		break;
	case EFighterState::Victory:
		VelX = VelDepth = 0.f;
		PlayCharAnim(TEXT("victory"), true);
		break;
	case EFighterState::Jump:
		PlayCharAnim(TEXT("jump"), true);
		break;
	default:
		break;
	}
}

void ABrawlerFighter::TickEntity(float DeltaSeconds)
{
	StateTime += DeltaSeconds;
	InvulnerableTimer = FMath::Max(0.f, InvulnerableTimer - DeltaSeconds);
	BlinkTimer = (State == EFighterState::Dead) ? StateTime + 0.07f : (InvulnerableTimer > 0.f && Team == EBrawlerTeam::Player ? InvulnerableTimer : 0.f);

	if (ArmorHits > 0)
	{
		ArmorResetTimer -= DeltaSeconds;
		if (ArmorResetTimer <= 0.f)
		{
			ArmorHits = 0;
		}
	}

	switch (State)
	{
	case EFighterState::Idle:
	case EFighterState::Walk:
		TickControl(DeltaSeconds);
		if (State == EFighterState::Idle || State == EFighterState::Walk)
		{
			ApplyMovement(DeltaSeconds);
		}
		break;

	case EFighterState::Jump:
		TickControl(DeltaSeconds);
		if (State == EFighterState::Jump)
		{
			SetAnimFrame(VelZ > 0.f ? 0 : 1);
			TickAirPhysics(DeltaSeconds);
		}
		break;

	case EFighterState::Attack:
		TickAttack(DeltaSeconds);
		break;

	case EFighterState::Hurt:
		VelX = FMath::FInterpTo(VelX, 0.f, DeltaSeconds, 10.f);
		ApplyMovement(DeltaSeconds);
		if (StateTime >= HurtDuration)
		{
			EnterState(EFighterState::Idle);
		}
		break;

	case EFighterState::Grabbing:
		GrabTimer += DeltaSeconds;
		KeepGrabPartnerInPlace();
		TickControl(DeltaSeconds);
		if (State == EFighterState::Grabbing && (GrabTimer > 2.2f || !GrabPartner.IsValid() || GrabPartner->GetState() != EFighterState::Grabbed))
		{
			ReleaseGrab();
			EnterState(EFighterState::Idle);
		}
		break;

	case EFighterState::Grabbed:
		if (!GrabPartner.IsValid() || (GrabPartner->GetState() != EFighterState::Grabbing && GrabPartner->GetState() != EFighterState::Attack))
		{
			OnReleasedFromGrab();
		}
		break;

	case EFighterState::Falling:
		SetAnimFrame(VelZ > 0.f ? 0 : 1);
		TickAirPhysics(DeltaSeconds);
		if (bThrown)
		{
			ProcessThrownCollisions();
		}
		break;

	case EFighterState::Down:
		if (StateTime >= DownDuration)
		{
			if (Health <= 0.f)
			{
				EnterState(EFighterState::Dead);
				OnDied();
			}
			else
			{
				EnterState(EFighterState::GetUp);
			}
		}
		break;

	case EFighterState::GetUp:
		if (IsAnimFinished() && StateTime > 0.3f)
		{
			MakeInvulnerable(GetUpInvulnerability);
			EnterState(EFighterState::Idle);
		}
		break;

	case EFighterState::Pickup:
		if (StateTime > 0.25f)
		{
			EnterState(EFighterState::Idle);
		}
		break;

	case EFighterState::Dead:
	case EFighterState::Victory:
	default:
		break;
	}

	ClampPosition();
}

void ABrawlerFighter::ApplyMovement(float DeltaSeconds)
{
	PosX += VelX * DeltaSeconds;
	Depth += VelDepth * DeltaSeconds;
}

void ABrawlerFighter::ClampPosition()
{
	Depth = FMath::Clamp(Depth, Brawler::DepthMin, Brawler::DepthMax);

	if (const ABrawlerGameMode* GM = GetBrawlerGameMode())
	{
		if (bClampToView)
		{
			const float Margin = 40.f;
			PosX = FMath::Clamp(PosX, GM->GetViewMinX() + Margin, GM->GetViewMaxX() - Margin);
		}
	}
	PosX = FMath::Clamp(PosX, -400.f, Brawler::StageEndX + 400.f);
}

void ABrawlerFighter::TickAirPhysics(float DeltaSeconds)
{
	VelZ -= Brawler::Gravity * DeltaSeconds;
	Height += VelZ * DeltaSeconds;
	PosX += VelX * DeltaSeconds;
	Depth += VelDepth * DeltaSeconds;

	if (Height <= 0.f && VelZ <= 0.f)
	{
		Height = 0.f;
		OnLanded();
		VelZ = 0.f;
	}
}

void ABrawlerFighter::OnLanded()
{
	ABrawlerGameMode* GM = GetBrawlerGameMode();

	if (State == EFighterState::Falling)
	{
		if (!bBounced && VelZ < -500.f)
		{
			// Kleiner Aufprall-Huepfer wie in SoR4
			bBounced = true;
			VelZ = 280.f;
			VelX *= 0.45f;
			Height = 0.1f;
			if (GM)
			{
				GM->SpawnEffect(TEXT("FX_Dust"), PosX, Depth, 0.f, Facing, 14.f);
				GM->PlaySfx(TEXT("SFX_Thud"), 0.8f);
				GM->ShakeCamera(4.f, 0.12f);
			}
			if (bThrown)
			{
				bThrown = false;
				Health = FMath::Max(0.f, Health - 12.f);
			}
			return;
		}
		bThrown = false;
		bBounced = false;
		EnterState(EFighterState::Down);
		if (Health <= 0.f)
		{
			DownDuration = 1.0f;
			if (GM)
			{
				GM->PlaySfx(TEXT("SFX_KO"), 0.7f, 0.2f);
			}
		}
		return;
	}

	if (State == EFighterState::Attack || State == EFighterState::Jump)
	{
		if (State == EFighterState::Attack)
		{
			State = EFighterState::Idle;
			OnAttackFinished();
			if (State != EFighterState::Idle)
			{
				return;
			}
		}
		VelX = VelDepth = 0.f;
		if (GM)
		{
			GM->SpawnEffect(TEXT("FX_Dust"), PosX, Depth, 0.f, Facing, 16.f, 0.6f);
		}
		EnterState(EFighterState::Idle);
	}
}

// ---------------------------------------------------------------------------
// Angriffe
// ---------------------------------------------------------------------------
void ABrawlerFighter::StartAttack(const FBrawlerAttack& Attack)
{
	CurrentAttack = Attack;
	bAttackConnected = false;
	LastActiveFrame = -1;
	HitThisAttack.Reset();

	const EFighterState Prev = State;
	State = EFighterState::Attack;
	StateTime = 0.f;
	if (Prev != EFighterState::Jump && Height <= 0.f)
	{
		VelX = VelDepth = 0.f;
	}

	float FPS;
	bool bLoop;
	GetAnimInfo(Attack.Anim, FPS, bLoop);
	if (Attack.FPS > 0.f)
	{
		FPS = Attack.FPS;
	}
	PlayFrames(SpriteSet, SpriteSet + TEXT("_") + Attack.Anim.ToString(), FPS, Attack.bLoopAnim, true);

	if (Attack.HealthCost > 0.f)
	{
		Health = FMath::Max(1.f, Health - Attack.HealthCost);
	}
	if (Attack.bWhoosh)
	{
		if (ABrawlerGameMode* GM = GetBrawlerGameMode())
		{
			GM->PlaySfx(TEXT("SFX_Whoosh"), 0.45f, 0.15f);
		}
	}
}

void ABrawlerFighter::TickAttack(float DeltaSeconds)
{
	const bool bAirborne = Height > 0.f || VelZ > 0.f;

	// Vorwaertsbewegung waehrend der aktiven Frames
	if (!bAirborne)
	{
		const bool bActive = AnimFrame >= CurrentAttack.ActiveStart - 1 && AnimFrame <= CurrentAttack.ActiveEnd;
		VelX = (bActive ? CurrentAttack.Lunge : 0.f) * Facing;
		VelDepth = 0.f;
		ApplyMovement(DeltaSeconds);
	}

	OnAttackFrame();
	if (State != EFighterState::Attack)
	{
		return;
	}
	ProcessAttackHits();

	if (bAirborne)
	{
		TickAirPhysics(DeltaSeconds);
		return;
	}

	const bool bDone = CurrentAttack.bLoopAnim ? StateTime >= CurrentAttack.Duration : IsAnimFinished() && StateTime > 0.05f;
	if (bDone)
	{
		State = EFighterState::Idle;
		OnAttackFinished();
		if (State == EFighterState::Idle)
		{
			EnterState(EFighterState::Idle);
		}
	}
}

void ABrawlerFighter::ProcessAttackHits()
{
	const bool bActive = CurrentAttack.bLoopAnim
		? true
		: (AnimFrame >= CurrentAttack.ActiveStart && AnimFrame <= CurrentAttack.ActiveEnd);
	if (!bActive)
	{
		return;
	}

	if (CurrentAttack.bMultiHit && AnimFrame != LastActiveFrame)
	{
		HitThisAttack.Reset();
	}
	LastActiveFrame = AnimFrame;

	for (TActorIterator<ABrawlerEntity> It(GetWorld()); It; ++It)
	{
		ABrawlerEntity* Target = *It;
		if (Target == this || !IsValid(Target) || !Target->IsHittable(Team))
		{
			continue;
		}
		if (HitThisAttack.Contains(Target))
		{
			continue;
		}
		// Gepackte Gegner koennen nur vom Greifer getroffen werden (Knie) – andere Gegner treffen sie nicht
		if (ABrawlerFighter* F = Cast<ABrawlerFighter>(Target))
		{
			if (F->GetState() == EFighterState::Grabbed && F->GetGrabPartner() != this && Team != EBrawlerTeam::Player)
			{
				continue;
			}
		}

		const float HalfW = Target->GetHurtHalfWidth();
		const float Fwd = (Target->PosX - PosX) * Facing;
		const bool bFront = Fwd + HalfW >= CurrentAttack.ReachMin && Fwd - HalfW <= CurrentAttack.ReachMax;
		const bool bBack = -Fwd + HalfW >= CurrentAttack.ReachMin && -Fwd - HalfW <= CurrentAttack.ReachMax;
		const bool bHoriz = CurrentAttack.bHitsBothSides ? (bFront || bBack) : (CurrentAttack.bHitsBehind ? bBack : bFront);
		if (!bHoriz)
		{
			continue;
		}
		if (FMath::Abs(Target->Depth - Depth) > CurrentAttack.DepthRange)
		{
			continue;
		}
		const float AMin = Height + CurrentAttack.HeightMin;
		const float AMax = Height + CurrentAttack.HeightMax;
		const float TMin = Target->Height;
		const float TMax = Target->Height + Target->GetHurtHeight();
		if (AMax < TMin || AMin > TMax)
		{
			continue;
		}

		float Dir = FMath::Sign(Target->PosX - PosX);
		if (Dir == 0.f)
		{
			Dir = Facing;
		}
		if (Target->ReceiveHit(this, CurrentAttack, Dir))
		{
			HitThisAttack.Add(Target);
			bAttackConnected = true;
			AddHitstop(CurrentAttack.Hitstop);
			if (!CurrentAttack.Weapon.IsNone() && Team == EBrawlerTeam::Player && Cast<ABrawlerFighter>(Target))
			{
				UseWeaponHit();
			}
			OnAttackHit(Target, CurrentAttack);
		}
	}
}

// ---------------------------------------------------------------------------
// Treffer einstecken
// ---------------------------------------------------------------------------
bool ABrawlerFighter::IsHittable(EBrawlerTeam AttackerTeam) const
{
	if (AttackerTeam == Team || !IsAlive() || IsInvulnerable())
	{
		return false;
	}
	switch (State)
	{
	case EFighterState::Down:
	case EFighterState::GetUp:
	case EFighterState::Dead:
		return false;
	case EFighterState::Falling:
		return !bThrown; // Jonglieren erlaubt
	default:
		return true;
	}
}

float ABrawlerFighter::GetHurtHeight() const
{
	return State == EFighterState::Falling ? 90.f : Brawler::BodyHeight;
}

bool ABrawlerFighter::ReceiveHit(ABrawlerFighter* Attacker, const FBrawlerAttack& Attack, float Direction)
{
	if (!Attacker || !IsHittable(Attacker->Team))
	{
		return false;
	}

	ABrawlerGameMode* GM = GetBrawlerGameMode();
	const float Damage = Attack.Damage;
	Health = FMath::Max(0.f, Health - Damage);

	const bool bHeavyFx = Attack.HitType != EHitType::Light || Health <= 0.f;
	if (GM)
	{
		const float FxHeight = FMath::Clamp(Attacker->Height + (Attack.HeightMin + Attack.HeightMax) * 0.5f - Height, 40.f, 170.f) + Height;
		GM->SpawnEffect(bHeavyFx ? TEXT("FX_HitBig") : TEXT("FX_HitSpark"), PosX - Direction * 18.f, Depth, FxHeight, Direction, 22.f);
		GM->PlaySfx(bHeavyFx ? TEXT("SFX_HitHeavy") : TEXT("SFX_HitLight"), bHeavyFx ? 1.f : 0.8f, 0.12f);
		if (bHeavyFx)
		{
			GM->ShakeCamera(6.f, 0.15f);
		}
		GM->OnDamageDealt(Attacker, this, Damage);
	}

	AddHitstop(Attack.Hitstop * 1.15f);
	OnHurt(Attacker, Damage);

	const bool bWasGrabbedByAttacker = State == EFighterState::Grabbed && GrabPartner.Get() == Attacker;

	// Wer gerade jemanden haelt, laesst los
	if (State == EFighterState::Grabbing || (State == EFighterState::Attack && GrabPartner.IsValid()))
	{
		ReleaseGrab();
	}

	if (Health <= 0.f)
	{
		Knockdown(Direction, FMath::Max(Attack.Knockback, 260.f), FMath::Max(Attack.Launch, 620.f));
		return true;
	}

	if (Attack.HitType == EHitType::Knockdown || State == EFighterState::Falling)
	{
		const float Launch = State == EFighterState::Falling ? FMath::Max(Attack.Launch * 0.6f, 420.f) : Attack.Launch;
		Knockdown(Direction, FMath::Max(Attack.Knockback, 160.f), FMath::Max(Launch, 380.f));
		return true;
	}

	if (bWasGrabbedByAttacker)
	{
		// Knie im Griff: bleibt gepackt, zuckt nur
		PlayCharAnim(TEXT("grabbed"), true);
		return true;
	}

	if (Armor > 0 && ArmorHits < Armor && State != EFighterState::Hurt)
	{
		// Super-Armor: Treffer wird eingesteckt, ohne unterbrochen zu werden
		++ArmorHits;
		ArmorResetTimer = 1.5f;
		return true;
	}
	ArmorHits = 0;

	if (State == EFighterState::Grabbed)
	{
		OnReleasedFromGrab();
	}

	Facing = -Direction;
	HurtDuration = Attack.HitType == EHitType::Heavy ? 0.5f : 0.34f;
	EnterState(EFighterState::Hurt);
	VelX = Direction * Attack.Knockback;
	VelDepth = 0.f;
	if (Height > 0.f)
	{
		// In der Luft getroffen -> immer umfallen
		Knockdown(Direction, 160.f, 300.f);
	}
	return true;
}

void ABrawlerFighter::Knockdown(float Direction, float Speed, float Launch)
{
	if (State == EFighterState::Grabbing || GrabPartner.IsValid())
	{
		ReleaseGrab();
	}
	GrabPartner.Reset();
	DropWeapon();

	Facing = -Direction;
	VelX = Direction * Speed;
	VelDepth = 0.f;
	VelZ = Launch;
	Height = FMath::Max(Height, 1.f);
	bBounced = false;
	DownDuration = 0.9f;
	EnterState(EFighterState::Falling);
}

// ---------------------------------------------------------------------------
// Griffe & Wuerfe
// ---------------------------------------------------------------------------
void ABrawlerFighter::StartGrab(ABrawlerFighter* Target)
{
	if (!Target)
	{
		return;
	}
	GrabPartner = Target;
	Target->OnGrabbedBy(this);
	EnterState(EFighterState::Grabbing);
	KeepGrabPartnerInPlace();
}

void ABrawlerFighter::ReleaseGrab()
{
	if (ABrawlerFighter* Partner = GrabPartner.Get())
	{
		GrabPartner.Reset();
		if (Partner->GetState() == EFighterState::Grabbed)
		{
			Partner->OnReleasedFromGrab();
		}
	}
	GrabPartner.Reset();
}

void ABrawlerFighter::OnGrabbedBy(ABrawlerFighter* Grabber)
{
	GrabPartner = Grabber;
	Facing = -Grabber->Facing;
	EnterState(EFighterState::Grabbed);
}

void ABrawlerFighter::OnReleasedFromGrab()
{
	GrabPartner.Reset();
	if (State == EFighterState::Grabbed)
	{
		MakeInvulnerable(0.3f);
		EnterState(EFighterState::Idle);
	}
}

void ABrawlerFighter::KeepGrabPartnerInPlace()
{
	if (ABrawlerFighter* Partner = GrabPartner.Get())
	{
		Partner->PosX = PosX + Facing * 52.f;
		Partner->Depth = Depth - 0.5f;
		Partner->Height = 0.f;
		Partner->Facing = -Facing;
	}
}

void ABrawlerFighter::GetThrown(ABrawlerFighter* InThrower, float Direction)
{
	GrabPartner.Reset();
	Thrower = InThrower;
	ThrownHits.Reset();
	Health = FMath::Max(0.f, Health - 10.f);
	Knockdown(Direction, 520.f, 560.f);
	bThrown = true;
	if (ABrawlerGameMode* GM = GetBrawlerGameMode())
	{
		GM->OnDamageDealt(InThrower, this, 10.f);
	}
}

void ABrawlerFighter::ProcessThrownCollisions()
{
	for (TActorIterator<ABrawlerFighter> It(GetWorld()); It; ++It)
	{
		ABrawlerFighter* Other = *It;
		if (Other == this || Other->Team != Team || !Other->IsAlive() || Other->IsDowned() || ThrownHits.Contains(Other))
		{
			continue;
		}
		if (FMath::Abs(Other->PosX - PosX) < 60.f && FMath::Abs(Other->Depth - Depth) < 30.f && Height < 160.f)
		{
			ThrownHits.Add(Other);
			FBrawlerAttack Crash;
			Crash.Damage = 12.f;
			Crash.HitType = EHitType::Knockdown;
			Crash.Knockback = 300.f;
			Crash.Launch = 500.f;
			Crash.HeightMin = 0.f;
			Crash.HeightMax = 150.f;
			Crash.Hitstop = 0.08f;
			// Der Werfer bekommt die Punkte
			ABrawlerFighter* Source = Thrower.IsValid() ? Thrower.Get() : this;
			if (Other->Team != Source->Team)
			{
				Other->ReceiveHit(Source, Crash, FMath::Sign(VelX) != 0.f ? FMath::Sign(VelX) : 1.f);
			}
		}
	}
}

// ---------------------------------------------------------------------------
// Waffen
// ---------------------------------------------------------------------------
void ABrawlerFighter::TakeWeapon(FName Type, int32 Durability)
{
	const FWeaponDef* Def = BrawlerData::GetWeapon(Type);
	if (!Def)
	{
		return;
	}
	Weapon = Type;
	WeaponDurability = Durability >= 0 ? Durability : Def->Durability;
	if (UBrawlerAssets* Assets = UBrawlerAssets::Get(this))
	{
		WeaponSprite->SetSprite(Assets->GetSprite(TEXT("Weapons"), TEXT("Weapon_") + Type.ToString()));
	}
	UpdateRender();
}

void ABrawlerFighter::DropWeapon(bool bPop)
{
	if (Weapon.IsNone())
	{
		return;
	}
	const FName Type = Weapon;
	const int32 Durability = WeaponDurability;
	Weapon = NAME_None;
	WeaponSprite->SetVisibility(false);

	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	Params.bDeferConstruction = true;
	if (ABrawlerWeaponItem* Item = GetWorld()->SpawnActor<ABrawlerWeaponItem>(ABrawlerWeaponItem::StaticClass(), FTransform::Identity, Params))
	{
		Item->Init(Type, Durability);
		Item->SetBeltPosition(PosX, Depth, FMath::Max(Height, 40.f));
		Item->FinishSpawning(FTransform::Identity);
		if (bPop)
		{
			Item->Pop(-Facing);
		}
	}
}

void ABrawlerFighter::ThrowWeapon()
{
	if (Weapon.IsNone())
	{
		return;
	}
	const FWeaponDef* Def = BrawlerData::GetWeapon(Weapon);
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	Params.bDeferConstruction = true;
	if (ABrawlerProjectile* P = GetWorld()->SpawnActor<ABrawlerProjectile>(ABrawlerProjectile::StaticClass(), FTransform::Identity, Params))
	{
		P->Init(Weapon, this, Def ? Def->ThrowDamage : 12.f, WeaponDurability);
		P->Facing = Facing;
		P->SetBeltPosition(PosX + Facing * 50.f, Depth, 120.f);
		P->FinishSpawning(FTransform::Identity);
	}
	Weapon = NAME_None;
	WeaponSprite->SetVisibility(false);
	if (ABrawlerGameMode* GM = GetBrawlerGameMode())
	{
		GM->PlaySfx(TEXT("SFX_Whoosh"), 0.8f, 0.1f);
	}
}

void ABrawlerFighter::UseWeaponHit()
{
	if (Weapon.IsNone())
	{
		return;
	}
	if (--WeaponDurability <= 0)
	{
		if (ABrawlerGameMode* GM = GetBrawlerGameMode())
		{
			GM->SpawnEffect(TEXT("FX_HitSpark"), PosX + Facing * 80.f, Depth, 110.f, Facing, 20.f);
			GM->PlaySfx(TEXT("SFX_Break"), 0.6f, 0.1f);
		}
		Weapon = NAME_None;
		WeaponSprite->SetVisibility(false);
	}
}

void ABrawlerFighter::OnAttackFrame()
{
	// Wurf: Waffe verlaesst die Hand im zweiten Frame
	if (CurrentAttack.Anim == FName(TEXT("weapon_throw")) && AnimFrame >= 1 && HasWeapon())
	{
		ThrowWeapon();
	}
}

void ABrawlerFighter::UpdateRender()
{
	Super::UpdateRender();

	if (Weapon.IsNone() || !Sprite->GetSprite())
	{
		WeaponSprite->SetVisibility(false);
		return;
	}

	UBrawlerAssets* Assets = UBrawlerAssets::Get(this);
	const FWeaponDef* Def = BrawlerData::GetWeapon(Weapon);
	FVector Anchor;
	FVector2D Size, Grip;
	if (!Assets || !Def || !Assets->GetHandAnchor(Sprite->GetSprite()->GetName(), Anchor) || !Assets->GetWeaponGrip(Weapon, Size, Grip))
	{
		WeaponSprite->SetVisibility(false);
		return;
	}

	// Sprite-Mitte relativ zum Griff (y nach oben), um den Waffenwinkel gedreht
	const float Theta = Anchor.Z + Def->HoldAngle;
	const float Rad = FMath::DegreesToRadians(Theta);
	const FVector2D C(Size.X * 0.5f - Grip.X, Grip.Y - Size.Y * 0.5f);
	const FVector2D R(C.X * FMath::Cos(Rad) - C.Y * FMath::Sin(Rad), C.X * FMath::Sin(Rad) + C.Y * FMath::Cos(Rad));

	// Gespiegelt bei Blick nach links: Mirror(Rot(t) v) = Rot(-t) Mirror(v)
	WeaponSprite->SetRelativeLocation(FVector(Facing * (Anchor.X + R.X), 2.f, Height + Anchor.Y + R.Y));
	WeaponSprite->SetRelativeRotation(FRotator(Facing * Theta, 0.f, 0.f));
	WeaponSprite->SetRelativeScale3D(FVector(Facing, 1.f, 1.f));
	WeaponSprite->SetTranslucentSortPriority(Sprite->TranslucencySortPriority + 1);
	WeaponSprite->SetVisibility(Sprite->IsVisible());
}
