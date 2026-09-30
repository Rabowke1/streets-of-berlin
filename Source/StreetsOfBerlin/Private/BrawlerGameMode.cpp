#include "BrawlerGameMode.h"

#include "BrawlerAssets.h"
#include "BrawlerCamera.h"
#include "BrawlerEffect.h"
#include "BrawlerEnemy.h"
#include "BrawlerHUD.h"
#include "BrawlerPlayer.h"
#include "BrawlerPlayerController.h"
#include "BrawlerProp.h"
#include "BrawlerStage.h"
#include "BrawlerWeaponItem.h"
#include "EngineUtils.h"
#include "StreetsOfBerlin.h"
#include "Components/AudioComponent.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/App.h"

namespace
{
	constexpr int32 MaxAttackers = 2;
}

ABrawlerGameMode::ABrawlerGameMode()
{
	PrimaryActorTick.bCanEverTick = true;
	DefaultPawnClass = nullptr;
	PlayerControllerClass = ABrawlerPlayerController::StaticClass();
	HUDClass = ABrawlerHUD::StaticClass();
}

// ---------------------------------------------------------------------------
// Ablauf
// ---------------------------------------------------------------------------
void ABrawlerGameMode::StartPlay()
{
	Super::StartPlay();

	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

	Stage = GetWorld()->SpawnActor<ABrawlerStage>(ABrawlerStage::StaticClass(), FTransform::Identity, Params);
	if (Stage)
	{
		Stage->Build(GetStageDef());
	}

	Camera = GetWorld()->SpawnActor<ABrawlerCamera>(ABrawlerCamera::StaticClass(), FTransform::Identity, Params);
	CameraX = Brawler::ScreenWidth * 0.5f;
	if (Camera)
	{
		Camera->SetView(CameraX, 0.f, 0.f);
	}
	if (Stage)
	{
		Stage->UpdateParallax(CameraX);
	}

	for (FConstPlayerControllerIterator It = GetWorld()->GetPlayerControllerIterator(); It; ++It)
	{
		if (APlayerController* PC = It->Get())
		{
			PC->SetViewTarget(Camera);
		}
	}

	SetFlow(EBrawlerFlow::Title);
}

void ABrawlerGameMode::HandleStartingNewPlayer_Implementation(APlayerController* NewPlayer)
{
	// Kein Pawn: die Spielfigur wird vom GameMode gespawnt und ueber den Controller gesteuert
	if (NewPlayer && Camera)
	{
		NewPlayer->SetViewTarget(Camera);
	}
}

void ABrawlerGameMode::SetFlow(EBrawlerFlow NewFlow)
{
	Flow = NewFlow;
	FlowTime = 0.f;
}

void ABrawlerGameMode::OnStartPressed()
{
	switch (Flow)
	{
	case EBrawlerFlow::Title:
		StartGame();
		break;
	case EBrawlerFlow::StageClear:
		if (FlowTime > 1.5f)
		{
			if (StageIndex + 1 < GetStageCount())
			{
				StartStage(StageIndex + 1);
			}
			else
			{
				SetFlow(EBrawlerFlow::Ending);
			}
		}
		break;
	case EBrawlerFlow::GameOver:
	case EBrawlerFlow::Ending:
		if (FlowTime > 1.5f)
		{
			UGameplayStatics::OpenLevel(this, FName(*UGameplayStatics::GetCurrentLevelName(this)));
		}
		break;
	default:
		break;
	}
}

void ABrawlerGameMode::StartGame()
{
	Score = 0;
	Lives = 3;
	StartStage(0);
}

void ABrawlerGameMode::ClearStageActors()
{
	TArray<AActor*> ToDestroy;
	for (TActorIterator<ABrawlerEntity> It(GetWorld()); It; ++It)
	{
		ToDestroy.Add(*It);
	}
	for (AActor* A : ToDestroy)
	{
		A->Destroy();
	}
	Enemies.Reset();
	AttackTokens.Reset();
	Player = nullptr;
}

void ABrawlerGameMode::StartStage(int32 Index)
{
	StageIndex = FMath::Clamp(Index, 0, GetStageCount() - 1);
	const FStageDef& Def = GetStageDef();

	ClearStageActors();
	NextEncounter = 0;
	ActiveEncounter = INDEX_NONE;
	CameraLockX = -1.f;
	CameraX = Brawler::ScreenWidth * 0.5f;
	bBossActive = false;
	GoArrowTimer = 0.f;
	RespawnTimer = -1.f;
	LastHitEnemy.Reset();
	ComboHits = 0;
	UGameplayStatics::SetGlobalTimeDilation(this, 1.f);

	if (Stage)
	{
		Stage->Build(Def);
		Stage->UpdateParallax(CameraX);
	}

	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	Params.bDeferConstruction = true;
	for (const FPropSpawn& P : Def.Props)
	{
		if (ABrawlerProp* Prop = GetWorld()->SpawnActor<ABrawlerProp>(ABrawlerProp::StaticClass(), FTransform::Identity, Params))
		{
			Prop->Init(P.Type, P.Drop);
			Prop->SetBeltPosition(P.X, P.Depth, 0.f);
			Prop->FinishSpawning(FTransform::Identity);
		}
	}
	for (const FWeaponSpawn& W : Def.Weapons)
	{
		if (ABrawlerWeaponItem* Item = GetWorld()->SpawnActor<ABrawlerWeaponItem>(ABrawlerWeaponItem::StaticClass(), FTransform::Identity, Params))
		{
			Item->Init(W.Type);
			Item->SetBeltPosition(W.X, W.Depth, 0.f);
			Item->FinishSpawning(FTransform::Identity);
		}
	}

	SpawnPlayer(260.f, 110.f, false);

	if (!Music || !Music->IsPlaying())
	{
		if (UBrawlerAssets* Assets = UBrawlerAssets::Get(this))
		{
			if (USoundBase* Track = Assets->GetSound(TEXT("MUS_Stage1")))
			{
				Music = UGameplayStatics::SpawnSound2D(this, Track, 0.5f);
			}
		}
	}
	SetFlow(EBrawlerFlow::Intro);
}

void ABrawlerGameMode::SpawnPlayer(float X, float Depth, bool bDropIn)
{
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	Params.bDeferConstruction = true;
	Player = GetWorld()->SpawnActor<ABrawlerPlayer>(ABrawlerPlayer::StaticClass(), FTransform::Identity, Params);
	if (Player)
	{
		Player->SetBeltPosition(X, Depth, 0.f);
		Player->FinishSpawning(FTransform::Identity);
		if (bDropIn)
		{
			Player->DropIn();
		}
	}
}

void ABrawlerGameMode::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	FlowTime += DeltaSeconds;

	if (SlowMoTimer > 0.f)
	{
		SlowMoTimer -= FApp::GetDeltaTime();
		if (SlowMoTimer <= 0.f)
		{
			UGameplayStatics::SetGlobalTimeDilation(this, 1.f);
		}
	}

	ComboTimer = FMath::Max(0.f, ComboTimer - DeltaSeconds);
	if (ComboTimer <= 0.f)
	{
		ComboHits = 0;
	}
	LastHitEnemyTimer = FMath::Max(0.f, LastHitEnemyTimer - DeltaSeconds);
	GoArrowTimer = FMath::Max(0.f, GoArrowTimer - DeltaSeconds);

	AttackTokens.RemoveAll([](const TWeakObjectPtr<ABrawlerEnemy>& E)
	{
		return !E.IsValid() || !E->IsAlive() || E->IsDowned();
	});
	Enemies.RemoveAll([](const TObjectPtr<ABrawlerEnemy>& E) { return !IsValid(E); });

	switch (Flow)
	{
	case EBrawlerFlow::Intro:
		if (FlowTime > 2.2f)
		{
			SetFlow(EBrawlerFlow::Playing);
		}
		break;
	case EBrawlerFlow::Playing:
		UpdateEncounters(DeltaSeconds);
		break;
	default:
		break;
	}

	if (RespawnTimer > 0.f)
	{
		RespawnTimer -= DeltaSeconds;
		if (RespawnTimer <= 0.f && Player)
		{
			Player->SetBeltPosition(CameraX - 250.f, 120.f, 0.f);
			Player->DropIn();
		}
	}

	UpdateCamera(DeltaSeconds);
}

// ---------------------------------------------------------------------------
// Kamera
// ---------------------------------------------------------------------------
void ABrawlerGameMode::UpdateCamera(float DeltaSeconds)
{
	const float HalfW = Brawler::ScreenWidth * 0.5f;
	float Target = CameraX;
	if (CameraLockX >= 0.f)
	{
		Target = CameraLockX;
	}
	else if (Player && Flow != EBrawlerFlow::Title)
	{
		// Nur vorwaerts scrollen (wie im Original)
		Target = FMath::Max(CameraX, Player->PosX + 120.f);
		const TArray<FEncounter>& Encounters = GetStageDef().Encounters;
		if (NextEncounter < Encounters.Num())
		{
			Target = FMath::Min(Target, Encounters[NextEncounter].LockCenterX);
		}
	}
	Target = FMath::Clamp(Target, HalfW, Brawler::StageEndX - HalfW);
	CameraX = FMath::FInterpTo(CameraX, Target, DeltaSeconds, 5.f);

	float SX = 0.f, SZ = 0.f;
	if (ShakeTime > 0.f)
	{
		ShakeTime -= DeltaSeconds;
		SX = FMath::FRandRange(-ShakeAmp, ShakeAmp);
		SZ = FMath::FRandRange(-ShakeAmp, ShakeAmp) * 0.6f;
	}

	if (Camera)
	{
		Camera->SetView(CameraX, SX, SZ);
	}
	if (Stage)
	{
		Stage->UpdateParallax(CameraX);
	}
}

void ABrawlerGameMode::ShakeCamera(float Amplitude, float Duration)
{
	ShakeAmp = FMath::Max(ShakeTime > 0.f ? ShakeAmp : 0.f, Amplitude);
	ShakeTime = FMath::Max(ShakeTime, Duration);
}

void ABrawlerGameMode::SlowMotion(float Dilation, float RealSeconds)
{
	UGameplayStatics::SetGlobalTimeDilation(this, Dilation);
	SlowMoTimer = RealSeconds;
}

// ---------------------------------------------------------------------------
// Kaempfe & Wellen
// ---------------------------------------------------------------------------
int32 ABrawlerGameMode::GetAliveEnemyCount() const
{
	int32 Count = 0;
	for (const TObjectPtr<ABrawlerEnemy>& E : Enemies)
	{
		if (IsValid(E) && E->IsAlive())
		{
			++Count;
		}
	}
	return Count;
}

void ABrawlerGameMode::UpdateEncounters(float DeltaSeconds)
{
	if (!Player)
	{
		return;
	}

	const TArray<FEncounter>& Encounters = GetStageDef().Encounters;
	if (ActiveEncounter == INDEX_NONE)
	{
		if (NextEncounter < Encounters.Num() && Player->PosX >= Encounters[NextEncounter].TriggerX)
		{
			ActiveEncounter = NextEncounter++;
			const FEncounter& E = Encounters[ActiveEncounter];
			CameraLockX = E.LockCenterX;
			GoArrowTimer = 0.f;
			bBossActive = E.bBoss;
			NextGroup = 0;
			GroupTimer = 0.f;
			if (E.Groups.Num() > 0)
			{
				SpawnGroup(E.Groups[0]);
				NextGroup = 1;
			}
		}
		return;
	}

	const FEncounter& E = Encounters[ActiveEncounter];
	GroupTimer += DeltaSeconds;
	const int32 Alive = GetAliveEnemyCount();

	if (NextGroup < E.Groups.Num())
	{
		const FSpawnGroup& G = E.Groups[NextGroup];
		// Erst spawnen, wenn die Kamera am Ziel ist
		const bool bCameraArrived = FMath::Abs(CameraX - CameraLockX) < 40.f;
		if (bCameraArrived && (Alive <= G.WhenAliveAtMost || GroupTimer >= G.MaxDelay))
		{
			SpawnGroup(G);
			++NextGroup;
			GroupTimer = 0.f;
		}
		return;
	}

	if (Alive == 0 && GroupTimer > 0.5f)
	{
		ActiveEncounter = INDEX_NONE;
		CameraLockX = -1.f;
		if (E.bBoss)
		{
			bBossActive = false;
			if (Player->IsAlive())
			{
				Player->Celebrate();
			}
			if (Music)
			{
				Music->FadeOut(2.f, 0.f);
			}
			SetFlow(EBrawlerFlow::StageClear);
		}
		else
		{
			GoArrowTimer = 3.5f;
			PlaySfx(TEXT("SFX_Go"), 0.8f, 0.f);
		}
	}
}

void ABrawlerGameMode::SpawnGroup(const FSpawnGroup& Group)
{
	int32 Index = 0;
	for (const FName& Type : Group.Enemies)
	{
		// Abwechselnd von rechts und links, Boss immer von rechts
		const bool bRight = (Index % 2 == 0) || ABrawlerEnemy::GetProfile(Type).bBoss;
		const float X = bRight ? GetViewMaxX() + 80.f + Index * 40.f : GetViewMinX() - 80.f - Index * 40.f;
		const float Depth = FMath::FRandRange(Brawler::DepthMin + 20.f, Brawler::DepthMax - 20.f);
		SpawnEnemy(Type, X, Depth);
		++Index;
	}
}

ABrawlerEnemy* ABrawlerGameMode::SpawnEnemy(FName Type, float X, float Depth)
{
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	Params.bDeferConstruction = true;
	ABrawlerEnemy* Enemy = GetWorld()->SpawnActor<ABrawlerEnemy>(ABrawlerEnemy::StaticClass(), FTransform::Identity, Params);
	if (Enemy)
	{
		Enemy->InitFromProfile(Type);
		Enemy->SetBeltPosition(X, Depth, 0.f);
		Enemy->Facing = X > CameraX ? -1.f : 1.f;
		Enemy->SetEntering(true);
		Enemy->FinishSpawning(FTransform::Identity);
		Enemies.Add(Enemy);
		if (Enemy->IsBoss())
		{
			LastHitEnemy = Enemy;
			LastHitEnemyTimer = 4.f;
		}
	}
	return Enemy;
}

bool ABrawlerGameMode::RequestAttackToken(ABrawlerEnemy* Enemy)
{
	if (AttackTokens.Contains(Enemy))
	{
		return true;
	}
	if (AttackTokens.Num() < MaxAttackers)
	{
		AttackTokens.Add(Enemy);
		return true;
	}
	return false;
}

void ABrawlerGameMode::ReleaseAttackToken(ABrawlerEnemy* Enemy)
{
	AttackTokens.Remove(Enemy);
}

// ---------------------------------------------------------------------------
// Punkte, Tod, Effekte
// ---------------------------------------------------------------------------
void ABrawlerGameMode::OnDamageDealt(ABrawlerFighter* Attacker, ABrawlerFighter* Victim, float Damage)
{
	if (Attacker && Attacker->Team == EBrawlerTeam::Player)
	{
		ComboHits = ComboTimer > 0.f ? ComboHits + 1 : 1;
		ComboTimer = 1.4f;
		Score += FMath::RoundToInt(Damage * 10.f) + ComboHits * 5;
		LastHitEnemy = Victim;
		LastHitEnemyTimer = 3.f;

		const ABrawlerEnemy* Enemy = Cast<ABrawlerEnemy>(Victim);
		if (Enemy && Enemy->IsBoss() && Victim->Health <= 0.f)
		{
			// Finaler Treffer gegen den Boss: Zeitlupe
			SlowMotion(0.25f, 1.4f);
			PlaySfx(TEXT("SFX_KO"), 1.f, 0.f);
		}
	}
	else if (Victim && Victim->Team == EBrawlerTeam::Player)
	{
		ComboHits = 0;
		ComboTimer = 0.f;
	}
}

void ABrawlerGameMode::OnEnemyKilled(ABrawlerEnemy* Enemy)
{
	if (!Enemy)
	{
		return;
	}
	Score += Enemy->GetEnemyProfile().Score;
	AttackTokens.Remove(Enemy);

	if (Enemy->IsBoss())
	{
		// Boss besiegt: alle uebrigen Gegner fallen um (wie in SoR)
		for (const TObjectPtr<ABrawlerEnemy>& Other : Enemies)
		{
			if (IsValid(Other) && Other != Enemy && Other->IsAlive())
			{
				Other->Health = 0.f;
				Other->Knockdown(Other->PosX > Enemy->PosX ? 1.f : -1.f, 250.f, 500.f);
			}
		}
	}
}

void ABrawlerGameMode::OnPlayerDied()
{
	--Lives;
	if (Lives > 0)
	{
		RespawnTimer = 1.0f;
	}
	else
	{
		if (Music)
		{
			Music->FadeOut(1.5f, 0.f);
		}
		SetFlow(EBrawlerFlow::GameOver);
	}
}

void ABrawlerGameMode::SpawnEffect(const FString& Prefix, float X, float Depth, float Height, float Facing, float FPS, float Scale)
{
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	Params.bDeferConstruction = true;
	if (ABrawlerEffect* Fx = GetWorld()->SpawnActor<ABrawlerEffect>(ABrawlerEffect::StaticClass(), FTransform::Identity, Params))
	{
		const bool bInFront = Prefix.StartsWith(TEXT("FX_Hit"));
		Fx->Init(Prefix, FPS, Scale, bInFront);
		Fx->Facing = Facing;
		Fx->SetBeltPosition(X, Depth, Height);
		Fx->FinishSpawning(FTransform::Identity);
	}
}

void ABrawlerGameMode::PlaySfx(const FString& Name, float Volume, float PitchVariance)
{
	if (UBrawlerAssets* Assets = UBrawlerAssets::Get(this))
	{
		if (USoundBase* Sound = Assets->GetSound(Name))
		{
			UGameplayStatics::PlaySound2D(this, Sound, Volume, 1.f + FMath::FRandRange(-PitchVariance, PitchVariance));
		}
	}
}
