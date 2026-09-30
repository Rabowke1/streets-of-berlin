#include "BrawlerCamera.h"

#include "BrawlerTypes.h"
#include "Camera/CameraComponent.h"

ABrawlerCamera::ABrawlerCamera()
{
	PrimaryActorTick.bCanEverTick = false;

	Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
	SetRootComponent(Camera);

	Camera->ProjectionMode = ECameraProjectionMode::Orthographic;
	Camera->OrthoWidth = Brawler::ScreenWidth;
	Camera->AspectRatio = Brawler::ScreenWidth / Brawler::ScreenHeight;
	Camera->bConstrainAspectRatio = true;
	Camera->SetRelativeRotation(FRotator(0.f, -90.f, 0.f));

	// Sprites sollen exakt ihre Farben behalten: keine Auto-Belichtung, kein Filmic-Tonemapping
	FPostProcessSettings& PP = Camera->PostProcessSettings;
	PP.bOverride_AutoExposureMethod = true;
	PP.AutoExposureMethod = EAutoExposureMethod::AEM_Manual;
	PP.bOverride_AutoExposureApplyPhysicalCameraExposure = true;
	PP.AutoExposureApplyPhysicalCameraExposure = false;
	PP.bOverride_AutoExposureBias = true;
	PP.AutoExposureBias = 0.f;
	PP.bOverride_ToneCurveAmount = true;
	PP.ToneCurveAmount = 0.f;
	PP.bOverride_ExpandGamut = true;
	PP.ExpandGamut = 0.f;
	PP.bOverride_BloomIntensity = true;
	PP.BloomIntensity = 0.f;
	PP.bOverride_VignetteIntensity = true;
	PP.VignetteIntensity = 0.f;
	PP.bOverride_MotionBlurAmount = true;
	PP.MotionBlurAmount = 0.f;
	PP.bOverride_SceneFringeIntensity = true;
	PP.SceneFringeIntensity = 0.f;
	Camera->PostProcessBlendWeight = 1.f;
}

void ABrawlerCamera::SetView(float X, float ShakeX, float ShakeZ)
{
	SetActorLocation(FVector(X + ShakeX, Brawler::CameraY, Brawler::CameraZ + ShakeZ));
}
